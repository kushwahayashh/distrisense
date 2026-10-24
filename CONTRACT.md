# DistriSense Artifact Contract — Engine → App

The app never imports the engine. It only reads JSON files under `results/`.
This is deliberate: the UI keeps working while the engine is still being built,
and a broken model can be swapped out without touching the app.

```
results/
  index.json                 # list of available scenarios
  <scenario_id>/
    meta.json                # run metadata
    validation.json          # validator report
    forecast.json            # quantile forecasts + net targets
    plan.json                # shipments / unmet / blocked, per level
    risk_dial.json           # metrics for the 6 planning levels
    baselines.json           # LP vs pro-rata vs greedy
    evaluation.json          # pinball loss, calibration, expiry risk
```

Scenario ids: `normal`, `scarce`, `expiry`.

## index.json

```json
{
  "generated_at": "2026-10-24T18:00:00",
  "scenarios": [
    { "id": "normal", "name": "Normal", "path": "results/normal" }
  ]
}
```

## meta.json

```json
{
  "scenario_id": "normal",
  "scenario_name": "Normal",
  "planning_week": "2026-W44",
  "seed": 42,
  "forecaster_used": "baseline_ma4",
  "forecaster_scores": { "baseline_ma4": 3.84, "ml_gbm": 3.91 },
  "solver_status": "optimal",
  "solve_time_seconds": 0.42,
  "levels": ["P50", "P60", "P70", "P80", "P90", "P95"],
  "default_level": "P50",
  "network": { "warehouses": 3, "stores": 8, "skus": 5 },
  "latest_arrival_day": 2,
  "min_shelf_life_days": 3
}
```

`solver_status` is one of `optimal`, `feasible`, `infeasible`, `error`.
The app shows it verbatim — never hide a non-optimal status.

## validation.json

```json
{
  "ok": true,
  "files": [
    { "name": "products.csv", "rows": 5, "status": "ok", "errors": 0, "warnings": 0 }
  ],
  "checks": [
    { "id": "no_negative", "label": "No negative quantities", "passed": true, "detail": "" }
  ],
  "errors": [
    { "file": "routes.csv", "row": 12, "column": "unit_cost", "rule": "non_negative", "message": "..." }
  ],
  "warnings": [
    { "file": "demand_history.csv", "row": 173, "column": "units_sold", "rule": "short_series", "message": "..." }
  ]
}
```

Any non-empty `errors` means the engine must refuse to produce a plan.

## forecast.json

```json
{
  "rows": [
    {
      "store_id": "S1", "sku_id": "SKU01", "opening_units": 18,
      "p50": 104, "p60": 111, "p70": 119, "p80": 126, "p90": 135, "p95": 146,
      "target_p50": 86, "target_p90": 117
    }
  ]
}
```

Invariant: `p50 <= p60 <= ... <= p95` and all values `>= 0`.
`target_*` = `max(0, ceil(forecast) - opening_units)`.

## plan.json

```json
{
  "scenario_id": "normal",
  "levels": {
    "P50": {
      "shipments": [
        {
          "warehouse_id": "W1", "store_id": "S1", "sku_id": "SKU01",
          "batch_id": "W1-SKU01-B1", "units": 42,
          "unit_cost": 2, "freight": 84,
          "arrival_day": 1, "shelf_life_on_arrival": 9,
          "expiry_date": "2026-11-05"
        }
      ],
      "unmet": [
        { "store_id": "S3", "sku_id": "SKU02", "target_units": 120,
          "shipped_units": 90, "unmet_units": 30 }
      ],
      "blocked": { "route": 24, "lead_time": 36, "shelf_life": 18 },
      "totals": {
        "target_units": 3120, "shipped_units": 2890, "unmet_units": 230,
        "freight": 6120, "shipments": 214
      },
      "checker": { "passed": true, "violations": [] }
    }
  }
}
```

The app displays a plan **only** when `checker.passed` is true.
`blocked` counts batch–store options rejected by each eligibility rule.

## risk_dial.json

```json
{
  "draws": 200,
  "levels": [
    {
      "level": "P50", "freight": 6120,
      "realized_cost_mean": 9840, "realized_cost_p90": 11250,
      "fulfillment_mean": 0.921, "fulfillment_p10": 0.874,
      "shipped_units": 2890, "unmet_units": 230
    }
  ]
}
```

## baselines.json

```json
{
  "levels": ["P50"],
  "methods": [
    {
      "id": "lp", "name": "LP optimizer",
      "planned_objective": 8880, "realized_cost_mean": 9840,
      "fulfillment_mean": 0.921, "fulfillment_p10": 0.874,
      "freight": 6120, "unmet_units": 230, "checker_passed": true
    }
  ]
}
```

## evaluation.json

```json
{
  "pinball": {
    "scored_weeks": "41-52",
    "baseline_ma4": 3.84,
    "ml_gbm": 3.91,
    "selected": "baseline_ma4"
  },
  "calibration": [
    { "level": "P50", "nominal": 0.50, "observed": 0.53, "within_tolerance": true }
  ],
  "expiry_risk_units": 41
}
```

`within_tolerance` is `abs(observed - nominal) <= 0.10`, per the PRD.

## Swapping mock for real

1. Engine writes the files above into `results/<scenario>/`.
2. Engine writes `results/index.json`.
3. Restart the app. Nothing else changes.

`scripts/make_mock_results.py` produces a deterministic example of every file.
It is **not** the engine and must not be shipped as one.
