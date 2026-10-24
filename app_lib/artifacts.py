from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _load(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_index():
    return _load(RESULTS / "index.json")


def scenario_dir(scenario_id: str) -> Path:
    return RESULTS / scenario_id


def meta(scenario_id: str) -> dict:
    return _load(scenario_dir(scenario_id) / "meta.json") or {}


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
    return pd.DataFrame(data.get("rows", []))


def risk_df(scenario_id: str) -> pd.DataFrame:
    data = load_json(scenario_id, "risk_dial.json", {"levels": []})
    return pd.DataFrame(data.get("levels", []))


def baselines_df(scenario_id: str) -> pd.DataFrame:
    data = load_json(scenario_id, "baselines.json", {"methods": []})
    return pd.DataFrame(data.get("methods", []))
