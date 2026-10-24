# DistriSense — Stream C Integration Update

**For:** Streams A/B/D · **From:** Stream C (Streamlit app)

**Repository:** https://github.com/kushwahayashh/distrisense  
**Integration commit:** `6439a39` on `main`  
**Status:** UI integration support ready; actual engine artifacts still required.

## 1. What changed

- Added a **Demo / Engine results** selector in the sidebar.
- Kept mock and computed artifacts in separate directories. Engine mode never
  substitutes demo files when engine files are missing.
- Added central scenario-name translation without changing backend IDs.
- Added clear **Not available yet** states for missing validation, forecasts,
  delivery plans, and Risk Dial results.
- Added forecast checks for required fields, duplicate store–SKU pairs,
  finite/nonnegative quantities, integer opening stock, ordered quantiles, and
  correct P50/P90 targets.
- Failed-checker plans are hidden and cannot be exported.
- Added a full-planner activation gate for jointly accepted A/B/D results.
- Added synthetic-data labeling for both sources.

**Verification:** `python -m pytest -q` passed **31 tests** in the app repository.
These test app integration and existing artifact contracts, not the correctness
or availability of your forecasting/optimization implementation.

## 2. Important change: output destination

**Do not overwrite `results/`.** That directory remains the mock demo.

Deliver computed synthetic results into:

```text
engine_results/
  index.json
  normal/
  scarce_supply/
  expiry_trap/
```

Each scenario's complete artifact family is:

```text
meta.json          # A / integration: actual run metadata
validation.json    # A / integration: actual input-validation report
forecast.json      # A + B: forecasts with validated opening stock and targets
plan.json          # B: allocations, unmet units, blocked options, checker
risk_dial.json     # D: six planning levels evaluated against 200 draws
baselines.json     # B + D: evaluated LP / pro-rata / greedy results
evaluation.json    # A + D: forecast quality and decision metrics
```

The JSON shapes in `CONTRACT.md` remain applicable. Its older `results/` paths
refer to the demo examples; use **`engine_results/`** for computed deliveries.

## 3. Scenario mapping

The mapping lives in `app_lib/artifacts.py`:

| UI alias | Engine directory / canonical key |
|---|---|
| `normal` | `normal` |
| `scarce` | `scarce_supply` |
| `expiry` | `expiry_trap` |

Keep actual identifiers such as `S01` / `K01`. Do not rename them to match the
mock examples. No changes to Stream A's canonical forecast CSV are required.

## 4. Stream A: minimum forecast delivery

Keep generating `outputs/<scenario>/planning_forecast.csv` as agreed. Your
adapter should save the frontend payload to:

```text
engine_results/<canonical_scenario>/forecast.json
```

Required envelope and fields:

```json
{
  "rows": [
    {
      "store_id": "S01",
      "sku_id": "K01",
      "opening_units": 20,
      "p50": 48.7,
      "p60": 55,
      "p70": 60,
      "p80": 70,
      "p90": 77.96,
      "p95": 90,
      "target_p50": 29,
      "target_p90": 58
    }
  ]
}
```

**Illustrative numbers only.** Actual delivery must use actual computed
forecasts and B's validated opening stock for all 40 store–SKU pairs.

- Use all six **lowercase** quantile keys.
- `target = max(0, ceil(quantile) - opening_units)`.
- Extra target fields (`target_p60`, etc.) are fine.
- Opening stock must be nonnegative whole units.
- Do not fabricate stock, checker results, or evaluation metrics.

A valid forecast can be viewed before B/D finish. Full-planner activation is
not needed just to view forecasts. Missing plan/evaluation sections stay unavailable.

## 5. Full-planner activation (A + B + D)

Only after a complete end-to-end run is jointly checked, write
`engine_results/index.json` with:

```json
{
  "mock": false,
  "integration_validated": true,
  "scenarios": [
    {"id": "normal", "name": "Normal"},
    {"id": "scarce_supply", "name": "Scarce Supply"},
    {"id": "expiry_trap", "name": "Expiry Trap"}
  ]
}
```

For a selected scenario, the app requires all seven files to parse as JSON
objects before showing the full planner. The flags record team acceptance;
they **do not** execute a validator or replace the independent checker.

In addition, a plan's `checker.passed` must be true before its shipment table
or CSV export is available. Only set it after B's actual checker passes.

Never copy mock plans into `engine_results/` to satisfy the gate. Do not turn
on these flags while only forecasting is complete.

## 6. How to check the UI

From the DistriSense repository:

```bash
git pull origin main
source .venv/bin/activate
python -m pytest -q
streamlit run app.py
```

For a new checkout, first create a virtual environment and install
`requirements.txt` as described in `README.md`.

1. Select **Demo**: existing mock UI should still work.
2. Select **Engine results**: only files from `engine_results/` are read.
3. Select the scenario with your delivered files.
4. Check the forecast page; missing B/D results should remain unavailable.
5. After joint acceptance, check plans, exports, and Risk Dial.

**Test limitation:** the original `tests/test_contract.py` checks demo files in
`results/`. New tests cover source isolation, alias mapping, forecast validation,
activation flags, and page rendering. A green suite alone does **not** certify
an arbitrary engine delivery; validate its schemas and computational results
before setting the acceptance flags.

## 7. What to send back

**A:** Pushed commit hash, passing test output, and a generated `forecast.json`
using B's validated stock. Include genuine metadata/validation reports when ready.

**B:** Agreed supply/route/batch schemas and actual six-level plans with checker
results, blocked counts, freight, and recomputed unmet units.

**D:** Actual 200-draw Risk Dial and baseline comparisons, plus evaluation files.

Start with **one complete `normal` scenario** before integrating all three.
Coordinate any field changes before modifying the contract.

## 8. Reference files

- `CONTRACT.md` — exact artifact schemas and integration update.
- `engine_results/README.md` — destination and activation instructions.
- `app_lib/artifacts.py` — source selection, aliases, forecast validation.
- `tests/test_sources.py` — integration tests.

All computed results are still **synthetic-data results**, not real-world
performance. P90 remains a planning setting, not a fulfillment guarantee.
