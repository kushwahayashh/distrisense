# Next backend delivery — Scarce Supply and Expiry Trap

Normal is accepted and active in the app. This is the request for the two
remaining computed scenarios. Send this document to Rahul's backend chat.

## Scope

Produce complete, independently checked candidates for:

| App scenario | Backend directory | Expected stress |
|---|---|---|
| Scarce Supply | `scarce_supply` | Tight batch and route capacity |
| Expiry Trap | `expiry_trap` | Short shelf life and cheap expiring stock |

Use the same engine code accepted for Normal. Only scenario configuration,
generated supply/routes/batches, and expiry assumptions should differ. Do not
change historical demand: the six quantile forecasts must remain identical to
Normal, so scenario differences come from supply constraints, not from
re-forecasting favorable demand.

Do **not** modify or replace `engine_results/normal/` in the frontend, and do not
change the accepted Normal forecast.

## Delivery format

Open one PR per scenario (preferred) or one PR with both clearly separated. In
the backend repository, place each delivery at:

```
deliveries/<scenario>-candidate/
  README.md
  verify.py
  inputs/                  # frozen data, routes, stock, forecast/holdout outputs
  <canonical-scenario>/    # the seven UI-facing JSON files
    meta.json
    validation.json
    forecast.json
    plan.json
    risk_dial.json
    baselines.json
    evaluation.json
  <canonical-scenario>/audit/
    inventory_batches.csv
    routes.csv
    opening_stock.csv
    all_plans.json
    provenance.json
    ...                    # demand draws / evaluation evidence as for Normal
```

The seven UI files must follow `CONTRACT.md` exactly. Required specifics:

- `meta.json`: canonical `scenario_id`, six levels, solver status per level,
  `synthetic: true`, network counts, planning date/week.
- `validation.json`: `ok: true`, per-file rows/errors/warnings, no errors.
- `forecast.json`: all 40 store–SKU rows, non-crossing quantiles, targets
  recomputed from the accepted opening stock.
- `plan.json`: all six levels. Every level has `checker.passed: true` and an
  empty `violations` list. Include `unmet` rows (the app hides zero-shortage
  rows) and `blocked` counts for route, lead time, and shelf life.
- `risk_dial.json`: exactly 200 shared demand draws, all six levels, including
  fulfillment P10, mean cost, P90 cost, freight, shipped and unmet units.
- `baselines.json`: LP, pro-rata and greedy on identical inputs and the same
  shared draws; every method reports `checker_passed`.
- `evaluation.json`: pinball scores, calibration per level, expiry-risk units.

## Verification required in the PR

The PR description must include actual commands and results:

1. Full backend test suite from a **clean checkout**, with the pinned
   environment. Do not depend on ignored local `data/` or `outputs/`.
2. `python deliveries/<scenario>-candidate/verify.py`, which must independently:
   - re-run the checker on every level and every baseline plan against the
     original batches, routes and targets;
   - reproduce the shared demand draw matrix and all reported evaluations;
   - recompute the recommendation rule at the default 90% P10 threshold;
   - confirm code and frozen-input hashes.
3. A short measured table: recommended level, its fulfillment P10, mean realized
   cost, freight, target/shipped/unmet units, and the LP vs greedy vs pro-rata
   comparison.
4. Confirmation that no Normal artifact, forecast, or accepted input changed.

Test-only portability fixes are acceptable, but engine source changes must be
explained and reflected in provenance.

## Acceptance rule

Frontend will install the seven files into a **review copy**, not the active
directory. A scenario is activated only when:

- all seven files load and pass contract/UI checks;
- every displayed level has `checker.passed: true`;
- the app's pages render without exceptions in an isolated activated copy;
- CSV export/reimport preserves shipment values;
- the Risk Dial recommendation and baseline table agree;
- a failed-checker test still hides shipments;
- both owners explicitly accept that scenario.

Scarce Supply and Expiry Trap remain unavailable in Engine results mode until
their own acceptance is recorded in `engine_results/index.json`.
