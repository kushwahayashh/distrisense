"""Contract tests for engine artifacts.

These tests do not test the optimizer or the forecaster. They test that whatever
writes `results/` respects CONTRACT.md, so the app never renders a plan that
breaks the rules it claims to enforce.

Run:  pytest -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
LEVELS = ["P50", "P60", "P70", "P80", "P90", "P95"]
REQUIRED = [
    "meta.json",
    "validation.json",
    "forecast.json",
    "plan.json",
    "risk_dial.json",
    "baselines.json",
    "evaluation.json",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def index() -> dict:
    path = RESULTS / "index.json"
    if not path.exists():
        pytest.skip("No results/index.json — run scripts/make_mock_results.py")
    return load(path)


@pytest.fixture(scope="module")
def scenario_ids(index: dict) -> list[str]:
    return [s["id"] for s in index["scenarios"]]


def test_index_lists_scenarios(index: dict) -> None:
    assert index["scenarios"], "index.json must list at least one scenario"
    for scenario in index["scenarios"]:
        assert scenario["id"] and scenario["name"]
        assert (RESULTS / scenario["id"]).is_dir()


def test_every_scenario_has_all_files(scenario_ids: list[str]) -> None:
    for sid in scenario_ids:
        for name in REQUIRED:
            assert (RESULTS / sid / name).exists(), f"{sid} is missing {name}"


def test_forecast_quantiles_never_cross(scenario_ids: list[str]) -> None:
    for sid in scenario_ids:
        rows = load(RESULTS / sid / "forecast.json")["rows"]
        assert rows, f"{sid} has no forecast rows"
        for row in rows:
            values = [row[name.lower()] for name in LEVELS]
            assert all(v >= 0 for v in values), f"{sid}: negative forecast in {row}"
            assert values == sorted(values), f"{sid}: crossed quantiles in {row}"
            expected = max(0, row["p50"] - row["opening_units"])
            assert row["target_p50"] == expected, f"{sid}: target_p50 mismatch in {row}"


def test_plan_respects_hard_rules(scenario_ids: list[str]) -> None:
    for sid in scenario_ids:
        plan = load(RESULTS / sid / "plan.json")
        for level in LEVELS:
            assert level in plan["levels"], f"{sid}: missing level {level}"
            node = plan["levels"][level]

            assert node["checker"]["passed"], f"{sid}/{level}: checker did not pass"
            assert not node["checker"]["violations"]

            for shipment in node["shipments"]:
                units = shipment["units"]
                assert isinstance(units, int) and units > 0, f"{sid}/{level}: bad units"
                assert shipment["arrival_day"] <= 2, f"{sid}/{level}: late arrival"
                assert shipment["shelf_life_on_arrival"] >= 3, f"{sid}/{level}: short shelf life"

            totals = node["totals"]
            assert totals["unmet_units"] == max(
                0, totals["target_units"] - totals["shipped_units"]
            ), f"{sid}/{level}: unmet does not reconcile"
            assert sum(s["units"] for s in node["shipments"]) == totals["shipped_units"]
            assert sum(s["freight"] for s in node["shipments"]) == totals["freight"]


def test_risk_dial_covers_six_levels(scenario_ids: list[str]) -> None:
    for sid in scenario_ids:
        data = load(RESULTS / sid / "risk_dial.json")
        levels = data["levels"]
        assert [r["level"] for r in levels] == LEVELS, f"{sid}: wrong levels"
        assert data["draws"] > 0
        for row in levels:
            assert 0 <= row["fulfillment_p10"] <= 1
            assert 0 <= row["fulfillment_mean"] <= 1
            assert row["fulfillment_p10"] <= row["fulfillment_mean"]
            assert row["freight"] >= 0 and row["realized_cost_mean"] >= 0


def test_baselines_use_same_inputs(scenario_ids: list[str]) -> None:
    for sid in scenario_ids:
        methods = load(RESULTS / sid / "baselines.json")["methods"]
        ids = {m["id"] for m in methods}
        assert {"lp", "pro_rata", "greedy"} <= ids, f"{sid}: missing a baseline"
        for method in methods:
            assert method["checker_passed"], f"{sid}: {method['id']} failed the checker"
            assert method["planned_objective"] >= 0
            assert method["realized_cost_mean"] >= 0


def test_calibration_flag_is_consistent(scenario_ids: list[str]) -> None:
    for sid in scenario_ids:
        rows = load(RESULTS / sid / "evaluation.json")["calibration"]
        assert rows, f"{sid}: no calibration rows"
        for row in rows:
            within = abs(row["observed"] - row["nominal"]) <= 0.10
            assert row["within_tolerance"] == within, f"{sid}: bad calibration flag"


def test_validation_has_no_errors_when_plan_exists(scenario_ids: list[str]) -> None:
    for sid in scenario_ids:
        report = load(RESULTS / sid / "validation.json")
        if not report["errors"]:
            continue
        plan = load(RESULTS / sid / "plan.json")
        assert not any(plan["levels"].values()), (
            f"{sid}: validator reported blocking errors but a plan was produced"
        )
