# Saved engine results (synthetic data)

This directory is intentionally separate from `results/`, which holds the demo.
Choose **Engine results** in the sidebar to read this directory. Missing files
show an unavailable state; the app never substitutes demo data here.

Use canonical backend scenario directories:

```
engine_results/
  index.json
  normal/
  scarce_supply/
  expiry_trap/
```

Each scenario uses the seven JSON files defined in `../CONTRACT.md`. Preserve
the actual store and SKU IDs. The app does not run forecasting or optimization.

A partial `forecast.json` delivery is supported once it contains actual forecasts,
validated opening stock, and correct targets. Missing validation, plans, and
evaluations remain unavailable. Do not copy mock files into this directory.

## Full-planner activation

Only after A/B/D jointly validate a complete end-to-end run, write:

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

These flags record team acceptance; they do not run or replace the independent
checker. All seven files must exist and parse as JSON objects for the selected
scenario. A plan must also have a passing checker before its shipments display
or export. Forecast viewing does not require full-planner activation.

The sidebar aliases `scarce` and `expiry` map centrally to `scarce_supply` and
`expiry_trap`. Backend folder names and IDs remain unchanged.
