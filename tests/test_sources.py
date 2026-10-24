import json

import pytest
from streamlit.testing.v1 import AppTest

from app_lib import artifacts


def test_aliases_preserve_backend_names():
    assert artifacts.backend_scenario("scarce") == "scarce_supply"
    assert artifacts.backend_scenario("expiry") == "expiry_trap"
    assert artifacts.backend_scenario("scarce_supply") == "scarce_supply"
    with pytest.raises(ValueError):
        artifacts.backend_scenario("../outside")


def test_engine_never_falls_back_to_demo(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "ENGINE_RESULTS", tmp_path)
    monkeypatch.setattr(artifacts.st, "session_state", {"data_source": "Engine results"})
    assert artifacts.scenario_dir("scarce") == tmp_path / "scarce_supply"
    assert artifacts.forecast_df("normal").empty
    assert artifacts.plan("normal") == {"levels": {}}
    assert not artifacts.planner_ready("normal")


def test_complete_run_needs_explicit_acceptance(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "ENGINE_RESULTS", tmp_path)
    monkeypatch.setattr(artifacts.st, "session_state", {"data_source": "Engine results"})
    folder = tmp_path / "normal"
    folder.mkdir()
    for name in ("meta", "validation", "forecast", "plan", "risk_dial", "baselines", "evaluation"):
        (folder / f"{name}.json").write_text("{}")
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"mock": False}))
    assert not artifacts.planner_ready("normal")
    index.write_text(json.dumps({"mock": False, "integration_validated": True}))
    assert artifacts.planner_ready("normal")


def test_forecast_preserves_ids_and_ceil_targets(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "ENGINE_RESULTS", tmp_path)
    monkeypatch.setattr(artifacts.st, "session_state", {"data_source": "Engine results"})
    folder = tmp_path / "normal"
    folder.mkdir()
    row = {"store_id": "S01", "sku_id": "K01", "opening_units": 20,
           "p50": 48.7, "p60": 55, "p70": 60, "p80": 70, "p90": 77.96,
           "p95": 90, "target_p50": 29, "target_p90": 58}
    file = folder / "forecast.json"
    file.write_text(json.dumps({"rows": [row]}))
    frame = artifacts.forecast_df("normal")
    assert frame.iloc[0]["store_id"] == "S01"
    assert frame.iloc[0]["sku_id"] == "K01"
    row["target_p90"] = 57
    file.write_text(json.dumps({"rows": [row]}))
    with pytest.raises(ValueError, match="Incorrect target"):
        artifacts.forecast_df("normal")


@pytest.mark.parametrize("source", ["Demo", "Engine results"])
@pytest.mark.parametrize("scenario", ["normal", "scarce", "expiry"])
@pytest.mark.parametrize("page", ["data_validation", "plan_export", "risk_baselines"])
def test_pages_handle_both_sources(source, scenario, page):
    app = AppTest.from_file(str(artifacts.ROOT / "app_pages" / f"{page}.py"))
    app.session_state["data_source"] = source
    app.session_state["scenario_id"] = scenario
    app.run(timeout=30)
    assert not app.exception


def test_sidebar_source_switch():
    app = AppTest.from_file(str(artifacts.ROOT / "app.py")).run(timeout=30)
    app.sidebar.selectbox[0].select("Engine results").run(timeout=30)
    assert not app.exception
    assert app.session_state["data_source"] == "Engine results"
    assert any("not available yet" in message.value for message in app.info)
    app.sidebar.selectbox[0].select("Demo").run(timeout=30)
    assert not app.exception
