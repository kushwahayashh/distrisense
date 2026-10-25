"""Recheck this frozen delivery without fitting forecasts.

Two levels of evidence are available:

* default: verify the frozen source inputs, the delivery-time code snapshot and
  every recorded plan/evaluation using the current independent checker.
* ``--rebuild``: additionally rebuild the candidate with the current planner and
  prove the seven UI artifacts are identical apart from solver timings.

Run from the backend repository root:

    python deliveries/normal-candidate/verify.py
    python deliveries/normal-candidate/verify.py --rebuild
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src import config
from src.decision_evaluation import draw_demand, evaluate_plan, recommend
from src.plan_checker import check_plan
from src.supply import Supply, generate_supply, validate_supply

ARTIFACTS = ("meta", "validation", "forecast", "plan", "risk_dial", "baselines", "evaluation")


def _without_timings(value):
    """Drop wall-clock solver timings so two runs can be compared semantically."""
    if isinstance(value, dict):
        return {
            key: _without_timings(item)
            for key, item in value.items()
            if key != "solve_time_seconds"
        }
    if isinstance(value, list):
        return [_without_timings(item) for item in value]
    return value


def check(rebuild: bool = False) -> None:
    delivery = Path(__file__).resolve().parent
    candidate = delivery / "normal"
    load = lambda name: json.loads((candidate / name).read_text())
    provenance = load("audit/provenance.json")

    # The repository code has moved on deliberately (the planner is now
    # scenario-parameterized). Check the delivery against the code snapshot that
    # actually produced it, kept under frozen-code/.
    frozen = delivery / "frozen-code"
    for relative, digest in provenance["code_sha256"].items():
        path = frozen / relative
        assert path.exists(), f"missing frozen code: {relative}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == digest, f"frozen code hash changed: {relative}"

    for original, digest in provenance["source_sha256"].items():
        parts = Path(original).parts
        start = next(
            i for i, part in enumerate(parts)
            if part in ("data", "outputs", "engine_results")
        )
        snapshot = delivery / "inputs" / Path(*parts[start:])
        actual = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        assert actual == digest, f"input hash changed: {snapshot}"

    data = delivery / "inputs/data/normal"
    locations, products, stock = [
        pd.read_csv(data / f"{name}.csv")
        for name in ("locations", "products", "opening_stock")
    ]
    audit = candidate / "audit"
    supply = Supply(
        pd.read_csv(audit / "inventory_batches.csv"),
        pd.read_csv(audit / "routes.csv"),
        pd.read_csv(audit / "opening_stock.csv"),
    )
    validate_supply(supply, locations, products).raise_if_invalid()
    regenerated = generate_supply(locations, products, stock, "normal")
    for name in ("batches", "routes", "opening_stock"):
        pd.testing.assert_frame_equal(getattr(supply, name), getattr(regenerated, name))

    forecast = load("forecast.json")
    frozen_forecast = json.loads(
        (delivery / "inputs/engine_results/normal/forecast.json").read_text()
    )
    assert forecast == frozen_forecast, "forecast changed after freeze"

    pairs = [(row["store_id"], row["sku_id"]) for row in forecast["rows"]]
    draws = draw_demand(pd.read_csv(data / "hidden_truth.csv"), pairs)
    np.testing.assert_array_equal(
        draws.values, np.load(audit / "demand_draws.npy", allow_pickle=False)
    )
    assert draws.digest == provenance["demand"]["sha256"]

    all_plans = load("audit/all_plans.json")
    comparisons = load("audit/all_level_comparisons.json")
    plan, risk = load("plan.json"), load("risk_dial.json")
    assert list(all_plans) == list(config.QUANTILE_COLUMNS)
    count = 0
    for level, methods in all_plans.items():
        targets = {
            (row["store_id"], row["sku_id"]): row[f"target_{level.lower()}"]
            for row in forecast["rows"]
        }
        assert set(methods) == {"lp", "greedy", "pro_rata"}
        for method, checked in methods.items():
            assert check_plan(checked, supply, targets)["passed"], (level, method)
            actual = evaluate_plan(checked, stock, draws)
            saved = next(row for row in comparisons[level] if row["id"] == method)
            assert all(actual[key] == saved[key] for key in actual), (level, method)
            assert (
                methods["lp"]["solver"]["continuous_objective"]
                <= checked["solver"]["continuous_objective"] + 1e-6
            ), (level, method)
            if method == "lp":
                assert checked == plan["levels"][level]
                saved_risk = next(row for row in risk["levels"] if row["level"] == level)
                assert all(actual[key] == saved_risk[key] for key in actual)
            count += 1

    assert load("baselines.json")["methods"] == comparisons["P50"]
    assert recommend(risk["levels"], risk["default_threshold"]) == risk["recommended_level"]
    assert not (candidate.parent / "index.json").exists()
    print(
        f"PASS: {count} independently checked plans; shared 200 x 40 demand draws; "
        "frozen code and source hashes match."
    )
    print("PASS: all-level evaluations, LP bounds, P50 comparisons and Risk Dial agree.")

    if rebuild:
        _check_current_code_rebuild(delivery)

    print("Not frontend acceptance: activation remains off.")


def _check_current_code_rebuild(delivery: Path) -> None:
    """Prove the current, scenario-parameterized planner reproduces the delivery."""
    from src.planner import build_candidate

    root = delivery / "inputs"
    with tempfile.TemporaryDirectory() as tmp:
        built = Path(build_candidate(
            Path(tmp),
            data_dir=root / "data/normal",
            output_dir=root / "outputs/normal",
            accepted_forecast=root / "engine_results/normal/forecast.json",
            scenario="normal",
        ))
        for name in ARTIFACTS:
            saved = json.loads((delivery / "normal" / f"{name}.json").read_text())
            fresh = json.loads((built / f"{name}.json").read_text())
            assert _without_timings(saved) == _without_timings(fresh), name
    print("PASS: current planner rebuilds all seven artifacts identically (timings excluded).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="also rebuild with the current planner and compare artifacts",
    )
    args = parser.parse_args()
    check(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
