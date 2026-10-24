from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
ENGINE_RESULTS = ROOT / "engine_results"
SCENARIOS = {"normal": "Normal", "scarce": "Scarce Supply", "expiry": "Expiry Trap"}
BACKEND_SCENARIOS = {"normal": "normal", "scarce": "scarce_supply", "expiry": "expiry_trap"}


def backend_scenario(scenario_id: str) -> str:
    if scenario_id in BACKEND_SCENARIOS:
        return BACKEND_SCENARIOS[scenario_id]
    if scenario_id in BACKEND_SCENARIOS.values():
        return scenario_id
    raise ValueError(f"Unknown scenario: {scenario_id}")


def source_root() -> Path:
    return ENGINE_RESULTS if st.session_state.get("data_source") == "Engine results" else RESULTS


def _load(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_index():
    return _load(source_root() / "index.json")


def scenario_dir(scenario_id: str) -> Path:
    canonical = backend_scenario(scenario_id)
    alias = next(k for k, v in BACKEND_SCENARIOS.items() if v == canonical)
    return source_root() / (canonical if source_root() == ENGINE_RESULTS else alias)


def meta(scenario_id: str) -> dict:
    return load_json(scenario_id, "meta.json", {})


def planner_ready(scenario_id: str) -> bool:
    if source_root() != ENGINE_RESULTS:
        return True
    index = load_index() or {}
    required = ("meta.json", "validation.json", "forecast.json", "plan.json",
                "risk_dial.json", "baselines.json", "evaluation.json")
    return (index.get("mock") is False
            and index.get("integration_validated") is True
            and all(isinstance(load_json(scenario_id, name), dict) for name in required))


def load_json(scenario_id: str, name: str, default=None):
    data = _load(scenario_dir(scenario_id) / name)
    return default if data is None else data


def validation(scenario_id: str) -> dict:
    return load_json(scenario_id, "validation.json", {})


def plan(scenario_id: str) -> dict:
    return load_json(scenario_id, "plan.json", {"levels": {}})


def evaluation(scenario_id: str) -> dict:
    return load_json(scenario_id, "evaluation.json", {})


def forecast_df(scenario_id: str) -> pd.DataFrame:
    data = load_json(scenario_id, "forecast.json", {"rows": []})
    frame = pd.DataFrame(data.get("rows", []))
    if frame.empty:
        return frame
    levels = ["p50", "p60", "p70", "p80", "p90", "p95"]
    required = ["store_id", "sku_id", "opening_units", *levels, "target_p50", "target_p90"]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Forecast is missing fields: {', '.join(sorted(missing))}")
    if frame.duplicated(["store_id", "sku_id"]).any():
        raise ValueError("Forecast contains duplicate store–SKU pairs.")
    numbers = frame[["opening_units", *levels, "target_p50", "target_p90"]].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numbers.to_numpy()).all() or (numbers < 0).any().any():
        raise ValueError("Forecast quantities must be finite, nonnegative numbers.")
    if (numbers["opening_units"] % 1 != 0).any():
        raise ValueError("Opening stock must contain whole units.")
    if (numbers[levels].diff(axis=1).iloc[:, 1:] < 0).any().any():
        raise ValueError("Forecast quantiles must not cross.")
    for level in ("p50", "p90"):
        expected = (np.ceil(numbers[level]) - numbers["opening_units"]).clip(lower=0)
        if not (numbers[f"target_{level}"] == expected).all():
            raise ValueError(f"Incorrect target_{level}: expected ceil(forecast) minus opening stock.")
    frame[numbers.columns] = numbers
    return frame


def risk_df(scenario_id: str) -> pd.DataFrame:
    data = load_json(scenario_id, "risk_dial.json", {"levels": []})
    return pd.DataFrame(data.get("levels", []))


def baselines_df(scenario_id: str) -> pd.DataFrame:
    data = load_json(scenario_id, "baselines.json", {"methods": []})
    return pd.DataFrame(data.get("methods", []))
