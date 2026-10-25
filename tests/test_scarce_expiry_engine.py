"""Acceptance tests for the computed Scarce Supply and Expiry Trap candidates."""
import io
import json
import shutil

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app_lib import artifacts

LEVELS = ["P50", "P60", "P70", "P80", "P90", "P95"]
SCENARIOS = {"scarce_supply": "scarce", "expiry_trap": "expiry"}


def load(scenario, name):
    path = artifacts.ROOT / "engine_results" / scenario / f"{name}.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_forecast_is_shared_with_accepted_normal(scenario):
    normal = json.loads((artifacts.ROOT / "engine_results/normal/forecast.json").read_text())
    assert load(scenario, "forecast") == normal


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_all_levels_are_checked_and_csv_round_trip(scenario):
    plan = load(scenario, "plan")
    assert plan["scenario_id"] == scenario
    assert list(plan["levels"]) == LEVELS
    for level in LEVELS:
        node = plan["levels"][level]
        assert node["checker"] == {"passed": True, "violations": []}
        assert node["solver"]["status"] == "optimal"
        assert all(node["blocked"][key] > 0 for key in ("route", "lead_time", "shelf_life"))
        shipments = pd.DataFrame(node["shipments"])
        decoded = pd.read_csv(io.StringIO(shipments.to_csv(index=False)))
        pd.testing.assert_frame_equal(shipments, decoded, check_dtype=False)
        assert (decoded.units % 1 == 0).all() and (decoded.units >= 0).all()
        assert (decoded.arrival_day <= 2).all()
        assert (decoded.shelf_life_on_arrival >= 3).all()
        totals = node["totals"]
        assert decoded.units.sum() == totals["shipped_units"]
        assert decoded.freight.sum() == totals["freight"]
        assert sum(r["unmet_units"] for r in node["unmet"]) == totals["unmet_units"]
        assert totals["target_units"] == totals["shipped_units"] + totals["unmet_units"]


def test_scarce_supply_is_short_and_reports_no_qualifying_level():
    risk = load("scarce_supply", "risk_dial")
    assert risk["draws"] == 200
    assert risk["recommended_level"] is None
    assert all(row["fulfillment_p10"] < risk["default_threshold"] for row in risk["levels"])
    plan = load("scarce_supply", "plan")["levels"]["P50"]
    assert plan["totals"]["unmet_units"] > 0
    comparison = load("scarce_supply", "baselines")
    methods = {row["id"]: row for row in comparison["methods"]}
    assert methods["lp"]["realized_cost_mean"] < methods["greedy"]["realized_cost_mean"]
    assert methods["lp"]["realized_cost_mean"] < methods["pro_rata"]["realized_cost_mean"]
    assert all(row["checker_passed"] for row in methods.values())


def test_expiry_trap_excludes_cheap_stock_and_recommends_p80():
    risk = load("expiry_trap", "risk_dial")
    assert risk["recommended_level"] == "P80"
    qualifying = [row for row in risk["levels"] if row["fulfillment_p10"] >= 0.9]
    assert min(qualifying, key=lambda row: row["realized_cost_mean"])["level"] == "P80"
    plan = load("expiry_trap", "plan")["levels"]["P50"]
    assert plan["blocked"]["shelf_life"] == 70
    assert plan["totals"]["unmet_units"] == 0
    comparison = load("expiry_trap", "baselines")
    methods = {row["id"]: row for row in comparison["methods"]}
    assert methods["lp"]["realized_cost_mean"] == methods["greedy"]["realized_cost_mean"]
    assert methods["lp"]["realized_cost_mean"] < methods["pro_rata"]["realized_cost_mean"]
    assert all(row["checker_passed"] for row in methods.values())


@pytest.fixture
def activated_copy(tmp_path, monkeypatch):
    """Activate a scenario only in an isolated copy; never modify the real index."""
    for scenario, alias in SCENARIOS.items():
        shutil.copytree(artifacts.ROOT / "engine_results" / scenario, tmp_path / scenario)
    (tmp_path / "index.json").write_text(json.dumps({
        "mock": False,
        "integration_validated": True,
        "scenarios": [{"id": scenario, "name": scenario} for scenario in SCENARIOS],
    }))
    monkeypatch.setattr(artifacts, "ENGINE_RESULTS", tmp_path)


def page_test(name, scenario):
    app = AppTest.from_file(str(artifacts.ROOT / "app_pages" / f"{name}.py"))
    app.session_state["data_source"] = "Engine results"
    app.session_state["scenario_id"] = SCENARIOS[scenario]
    return app.run(timeout=30)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_actual_pages_render(activated_copy, scenario):
    for name in ("data_validation", "plan_export", "risk_baselines"):
        app = page_test(name, scenario)
        assert not app.exception
        assert not app.error


def test_scarce_pages_show_shortage_and_no_qualifying_level(activated_copy):
    plan = page_test("plan_export", "scarce_supply")
    assert any("Independent checker passed" in message.value for message in plan.success)
    assert any("could not be covered" in message.value for message in plan.caption)
    risk = page_test("risk_baselines", "scarce_supply")
    assert any("No planning level reaches" in message.value for message in risk.warning)


def test_expiry_pages_show_blocked_stock_and_p80(activated_copy):
    plan = page_test("plan_export", "expiry_trap")
    assert any("Independent checker passed" in message.value for message in plan.success)
    assert any("No unmet units" in message.value for message in plan.success)
    risk = page_test("risk_baselines", "expiry_trap")
    assert any("**P80**" in message.value for message in risk.success)
    risk.slider[0].set_value(100).run(timeout=30)
    assert any("No planning level reaches" in message.value for message in risk.warning)


def test_failed_checker_hides_scarce_shipments(activated_copy):
    path = artifacts.ENGINE_RESULTS / "scarce_supply/plan.json"
    plan = json.loads(path.read_text())
    plan["levels"]["P50"]["checker"] = {
        "passed": False,
        "violations": [{"rule": "injected", "message": "review test"}],
    }
    path.write_text(json.dumps(plan))
    app = page_test("plan_export", "scarce_supply")
    assert not app.exception
    assert any("Checker failed" in message.value for message in app.error)
    assert not app.multiselect
