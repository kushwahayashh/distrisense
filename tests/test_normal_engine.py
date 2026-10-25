"""Acceptance tests for the actual Normal candidate, not demo artifacts.

The backend verifier separately rechecks all plans against original supply and
reproduces demand evaluation. These tests cover its frontend delivery.
"""
import csv
import io
import json
import math
import shutil

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app_lib import artifacts

LEVELS = ["P50", "P60", "P70", "P80", "P90", "P95"]
NORMAL = artifacts.ROOT / "engine_results/normal"


def load(name):
    return json.loads((NORMAL / f"{name}.json").read_text())


def test_computed_forecast_and_stock_agree():
    with (artifacts.ROOT / "data/normal/opening_stock.csv").open() as handle:
        stock = {(r["store_id"], r["sku_id"]): int(r["opening_units"]) for r in csv.DictReader(handle)}
    rows = load("forecast")["rows"]
    assert len(rows) == 40
    assert {(r["store_id"], r["sku_id"]) for r in rows} == set(stock)
    for row in rows:
        assert row["opening_units"] == stock[row["store_id"], row["sku_id"]]
        for level in LEVELS:
            assert row[f"target_{level.lower()}"] == max(0, math.ceil(row[level.lower()]) - row["opening_units"])


@pytest.mark.parametrize("level", LEVELS)
def test_plan_totals_and_csv_round_trip(level):
    plan = load("plan")["levels"][level]
    assert plan["checker"] == {"passed": True, "violations": []}
    assert plan["solver"]["status"] == "optimal"
    assert all(plan["blocked"][key] > 0 for key in ("route", "lead_time", "shelf_life"))
    shipments = pd.DataFrame(plan["shipments"])
    decoded = pd.read_csv(io.StringIO(shipments.to_csv(index=False)))
    pd.testing.assert_frame_equal(shipments, decoded, check_dtype=False)
    assert (decoded.units % 1 == 0).all() and (decoded.units >= 0).all()
    assert (decoded.arrival_day <= 2).all()
    assert (decoded.shelf_life_on_arrival >= 3).all()
    totals = plan["totals"]
    assert decoded.units.sum() == totals["shipped_units"]
    assert decoded.freight.sum() == totals["freight"]
    assert sum(r["unmet_units"] for r in plan["unmet"]) == totals["unmet_units"]
    assert totals["target_units"] == totals["shipped_units"] + totals["unmet_units"]


def test_recommendation_and_honest_baseline_tie():
    risk = load("risk_dial")
    assert risk["draws"] == 200
    assert [r["level"] for r in risk["levels"]] == LEVELS
    qualifying = [r for r in risk["levels"] if r["fulfillment_p10"] >= .9]
    assert min(qualifying, key=lambda r: r["realized_cost_mean"])["level"] == risk["recommended_level"] == "P80"
    comparison = load("baselines")
    assert comparison["levels"] == ["P50"]
    methods = {row["id"]: row for row in comparison["methods"]}
    assert methods["lp"]["realized_cost_mean"] == methods["greedy"]["realized_cost_mean"]
    assert all(r["checker_passed"] for r in methods.values())


def test_all_computed_scenarios_are_activated(monkeypatch):
    monkeypatch.setattr(artifacts.st, "session_state", {"data_source": "Engine results"})
    assert artifacts.planner_ready("normal")
    assert artifacts.planner_ready("scarce")
    assert artifacts.planner_ready("expiry")


def test_unaccepted_scenario_cannot_activate_just_by_copying_files(tmp_path, monkeypatch):
    shutil.copytree(NORMAL, tmp_path / "scarce_supply")
    (tmp_path / "index.json").write_text(json.dumps({
        "mock": False, "integration_validated": True,
        "scenarios": [{"id": "normal", "name": "Normal"}],
    }))
    monkeypatch.setattr(artifacts, "ENGINE_RESULTS", tmp_path)
    monkeypatch.setattr(artifacts.st, "session_state", {"data_source": "Engine results"})
    assert not artifacts.planner_ready("scarce")


@pytest.fixture
def accepted_review_copy(tmp_path, monkeypatch):
    """Test activation only in an isolated copy; never modify the real index."""
    shutil.copytree(NORMAL, tmp_path / "normal")
    (tmp_path / "index.json").write_text(json.dumps({"mock": False, "integration_validated": True}))
    monkeypatch.setattr(artifacts, "ENGINE_RESULTS", tmp_path)


def page_test(name):
    app = AppTest.from_file(str(artifacts.ROOT / "app_pages" / f"{name}.py"))
    app.session_state["data_source"] = "Engine results"
    app.session_state["scenario_id"] = "normal"
    return app.run(timeout=30)


def test_actual_pages_render_in_review_copy(accepted_review_copy):
    for name in ("data_validation", "plan_export", "risk_baselines"):
        app = page_test(name)
        assert not app.exception
        assert not app.error


@pytest.mark.parametrize("level", LEVELS)
def test_six_levels_show_checked_plan(accepted_review_copy, level):
    app = page_test("plan_export")
    app.radio[0].set_value(level).run(timeout=30)
    assert not app.exception
    assert any("Independent checker passed" in message.value for message in app.success)
    assert any("No unmet units" in message.value for message in app.success)


def test_risk_threshold_table_and_recommendation_agree(accepted_review_copy):
    app = page_test("risk_baselines")
    assert any("**P80**" in message.value for message in app.success)
    tables = [table.value for table in app.dataframe]
    risk = next(table for table in tables if "status" in table.columns)
    assert risk.loc[risk.status == "★ cheapest qualifying", "level"].tolist() == ["P80"]
    app.slider[0].set_value(100).run(timeout=30)
    assert not app.exception
    assert any("No planning level reaches" in message.value for message in app.warning)


def test_failed_checker_hides_shipments(accepted_review_copy):
    plan_path = artifacts.ENGINE_RESULTS / "normal/plan.json"
    plan = json.loads(plan_path.read_text())
    plan["levels"]["P50"]["checker"] = {"passed": False, "violations": [{"rule": "injected", "message": "review test"}]}
    plan_path.write_text(json.dumps(plan))
    app = page_test("plan_export")
    assert not app.exception
    assert any("Checker failed" in message.value for message in app.error)
    assert not app.multiselect
