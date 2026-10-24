# Normal scenario — synthetic opening stock

Send `opening_stock.csv` to Stream A. It is inventory input, not forecasts,
shipment allocations, or a complete supply/optimizer implementation.

## Assumptions and validation

- Seed: **42**, Python standard-library `random.Random`.
- Quantity assumption: uniformly generated integer **0–20 units**, inclusive,
  per store–SKU pair. This range is a documented prototype assumption, not a
  PRD-prescribed value or an observed business measurement.
- All 40 combinations of **S01–S08 × K01–K05**, one record each.
- IDs match Stream A's generator convention; network size matches its config
  at commit `5c22573eda8901c8abc3e308bf746d734446fb4e`.
- No demand forecasts, holdout scores, hidden truth, or evaluation results are
  used to choose stock quantities. Do not tune them to improve demo results.
- Header: `store_id,sku_id,opening_units`; nonnegative whole-unit quantities.
- Generator: `python scripts/make_opening_stock.py` from the DistriSense repo.
  It refuses to overwrite an existing file to protect received inventory.

## Stream A next step

Copy the CSV into **your forecasting repository** at
`data/normal/opening_stock.csv`. Activate that repository's environment and run:

```bash
python -m src.frontend_bridge normal --stock data/normal/opening_stock.csv
```

Return the generated `engine_results/normal/forecast.json` plus any bridge
validation errors. Stream A should also validate exact pair matching against
its actual generated forecast before export.

Keep using this same stock file for subsequent normal-scenario target and plan
calculations. Full-planner acceptance flags must remain off until B/D are done.
