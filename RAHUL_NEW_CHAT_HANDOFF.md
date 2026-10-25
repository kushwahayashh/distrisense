# DistriSense — Full Context for Rahul's New AI Chat

> **SUPERSEDED.** Do not upload this file. Read
> [`RAHUL_HANDOFF.md`](RAHUL_HANDOFF.md) instead. The engine now lives in
> `backend/` and the old backend repository is frozen. Kept for history;
> cleanup is deferred until after submission.

> Rahul: upload this entire file to your new AI chat. Also provide access to the
> backend repository and the final PRD. Ask the AI to inspect current code before
> changing anything. This file is a handoff, not proof that pending code exists.

## 1. Your task and working agreement

We are Team **Byte Works**, building **DistriSense** for Triwizathon 2026,
Problem Statement 2: Distribution Intelligence & Inventory Optimization.

The app owner and Rahul have agreed:

- **Rahul continues backend work in `rahullamani01/engine-module-`.** Forecasting
  is complete. Next responsibility is the missing **Stream B and Stream D** work:
  supply/routes, eligibility, shipment optimization, independent checking,
  allocation baselines, simulated evaluation, and Risk Dial artifacts.
- **The app owner continues Stream C in `kushwahayashh/distrisense`.** They own
  Streamlit, result reading, display/export, artifact integration and frontend QA.
- The app owner generated the accepted **opening-stock CSV only**. They did NOT
  implement an optimizer or Risk Dial engine. Do not assume those exist.
- Coordinate schema changes. Do not duplicate forecasting or silently change the
  accepted IDs, opening stock, forecasts, scenario names, or output contracts.

**First new-chat action:** inspect backend `main`, read the final PRD and frontend
contract, run existing tests, then implement B/D incrementally. Do not spend the
session inventing more handoff documents or repeating completed forecasting work.

## 2. Repositories and verified checkpoints

### Backend — Rahul

https://github.com/rahullamani01/engine-module-

Latest checked `main`: **`68c0f75a6383b2b3fb0d7ba771f6e0ef4212f173`**.
This commit updates README documentation, not forecasting logic.

Earlier checkpoints:

- `5c22573eda8901c8abc3e308bf746d734446fb4e`: forecasting implementation/test fix.
- `20ad5f1187f562c360a9bbef579558ce1332e238`: normal forecast JSON and initial README.
- `68c0f75`: README corrected to reflect completed Stream A and pending B/D.

The app owner's GitHub account `kushwahayashh` accepted write access to this repo
and pushed only that README update. Backend remains Rahul's working repository.

### Frontend — app owner

https://github.com/kushwahayashh/distrisense

Latest checked `main`: **`04e338e985d682d32eb07f9e05c275e4af01773d`**.

- `6439a39`: separate demo/engine sources and integration gates.
- `04e338e`: accepted normal forecast, opening stock, stock generator/tests and handoff.

Local frontend path on the app owner's machine:
`/home/eren/Travizthon/distrisense`.
Rahul's previously used path is `/Users/rahulchavan/Documents/DIE`; do not assume
this path exists in a new environment.

Commit hashes are checkpoints, not a reason to reset newer work. Fetch and inspect
current branches; preserve unrelated changes. Prefer focused branches and PRs.

## 3. Product in plain words

For one replenishment week, recommend **which warehouse batch sends which SKU,
to which store, in what quantity**, while respecting limited supply, shared route
capacity, active routes, arrival cutoffs and shelf life. A planner reviews and
exports; the software does not dispatch trucks.

Pipeline:

```text
Validate inputs → forecast demand ranges → subtract store stock → eligible options
→ LP allocation → floor whole units → independent checker
→ compare two allocation baselines using 200 common demand draws
→ save artifacts → Streamlit reads them
```

**Synthetic-data prototype only.** No real-world accuracy/savings/waste-reduction
claims. P90 is a planning setting, not a 90% fulfillment guarantee.

## 4. Source of truth and fixed configuration

The selected final PRD is authoritative. A copy is in the frontend repository:
`docs/Byte Works PRD.docx`; problem statement: `docs/problem-statement.md`.
Rahul may have the same final PRD named
`Byte_Works_PRD_v5_0___Round_1_Final-2.docx`. Compare if unsure; flag disagreements.

| Parameter | Value |
|---|---|
| Network | 3 warehouses, 8 stores, 5 SKUs, 2 regions |
| Backend IDs | stores S01–S08, SKUs K01–K05, warehouses W01–W03 |
| History | weeks 1–52; first 4 weeks warm-up |
| Fit / holdout / final refit | 5–40 / 41–52 / 5–52 |
| Planning | week 53 |
| Seed | 42 |
| Planning levels | P50, P60, P70, P80, P90, P95 |
| Lost-sale / overstock cost | ₹12 / ₹3 per unit |
| Freight / lead time defaults | ₹1–₹6 per unit / 0–3 days |
| Latest arrival / shelf life on arrival | day 2 / minimum 3 days |
| Evaluation | 200 seeded negative-binomial demand draws |
| Optimizer | `scipy.optimize.linprog(method="highs")` |

Derive actual dates from backend config/history; do not copy calendar dates from
frontend mock examples. Current backend history begins 2025-01-06. The old mock
UI's `2026-W44` label is NOT the real planning period.

All scenarios share historical demand. Supply/route/expiry differences distinguish
`normal`, `scarce_supply`, `expiry_trap`. Freeze synthetic supply assumptions before
viewing comparisons; do not tune stock or costs until the LP wins.

CPU only; Python, pandas, NumPy, scikit-learn, SciPy, pytest. Frontend additionally
uses Streamlit and Plotly. No database, separate frontend/API, GPU, or external AI
service is needed. Do not introduce dependencies without agreement.

## 5. Completed Stream A work — preserve it

Backend modules checked in the repository:

```text
src/config.py             src/schemas.py
src/data_generator.py     src/data_validation.py
src/baseline.py           src/features.py
src/quantile_model.py     src/metrics.py
src/evaluation.py         src/engine.py
src/targets.py            src/handoff.py
src/forecast_adapter.py   src/forecast_audit.py
src/frontend_bridge.py
```

Implemented: synthetic demand, validation, MA4 residual quantiles, Gradient
Boosting quantiles, holdout pinball selection, final refit, targets, audits,
forecast JSON conversion, frontend bridge.

**Verification provenance:** Rahul reported **112 backend tests passed in 19.59 s**
and all three scenario audits passed. These were not rerun as a combined backend
suite by Stream C. Stream C independently ran **37 frontend tests** and accepted
the normal forecast integration. Do not combine these counts into one suite or
claim full-planner verification.

Reported frozen-dataset holdout scores: MA4 mean pinball **4.9339**, GB **4.7109**.
GB selected for all three supply scenarios. Use actual saved metrics for export,
not these rounded chat numbers. A different run may select the baseline; never
hardcode ML superiority.

### Canonical forecast CSV

`outputs/<canonical_scenario>/planning_forecast.csv`

```text
store_id,sku_id,planning_week,method,P50,P60,P70,P80,P90,P95,used_pooled_residuals
```

40 unique pairs, planning week 53, finite nonnegative nondecreasing forecasts.
Preserve the CSV schema. Quantiles remain decimals; targets use ceilings.

## 6. Accepted opening stock and forecast

Both files are committed in the frontend repo:

```text
data/normal/opening_stock.csv
data/normal/OPENING_STOCK_NOTES.md
engine_results/normal/forecast.json
```

Opening-stock header: `store_id,sku_id,opening_units`.

Exactly 40 pairs, nonnegative integer units. Generated with seed 42 using Python
`random.Random`, uniform integer **0–20 inclusive**, in store/SKU sorted order.
This is a documented synthetic assumption, NOT a measured input or PRD-mandated
range. Generator: frontend `scripts/make_opening_stock.py`. Do not regenerate
different inventory or use zeros as a convenience during allocation.

Stream C checked the delivered forecast against this file:

- All 40 pairs and opening quantities match exactly.
- All six quantiles are ordered, finite and nonnegative.
- All six targets equal `max(0, ceil(quantile) - opening_units)`.
- Normal computed forecast renders in Streamlit; demo data remains unchanged.

**A → C normal forecast integration is accepted.** This does not mean shipment
plans or evaluations have been accepted.

Bridge usage in the backend repository, after saved forecasts and stock exist:

```bash
source .venv/bin/activate
python -m src.engine normal
python -m src.forecast_audit normal
python -m src.frontend_bridge normal --stock data/normal/opening_stock.csv
```

The bridge refuses to overwrite existing forecast JSON (one already exists in
backend `main`). Use `--results-dir candidate_engine_results` to produce a new
candidate rather than deleting accepted files.

## 7. Reproducibility warning discovered during preparation

The frontend environment currently has scikit-learn **1.9.1**. Rerunning backend
forecasting in that environment produced slightly different quantiles (maximum
difference about **2.17 units**) and GB pinball about **4.7126**, not the accepted
artifact's run. The accepted forecast was NOT overwritten.

Backend `requirements.txt` pins:

```text
numpy==2.4.4
pandas==3.0.2
scikit-learn==1.8.0
scipy==1.17.1
pytest>=8.0
```

Use backend's own virtual environment and pinned dependencies to reproduce its
outputs. Frontend intentionally uses pandas 2.x; do not force the two environments
to merge. Verify numerical agreement and record versions before replacing any
accepted artifact. A same seed alone does not guarantee cross-version equality.

During initial preparation, the app owner cloned backend to
`/tmp/opencode/engine-module-readme` and reran normal forecasting in a temporary
backend environment. These generated artifacts are uncommitted preparation work,
not an implemented optimizer. No B/D implementation was added or pushed. Work
was paused when Rahul took ownership.

## 8. Stream B — implement next

### Supply inputs and strict validation

Reuse accepted store inventory. Generate deterministic warehouse batches/routes
and validate against actual locations/products:

```text
inventory_batches.csv:
batch_id, warehouse_id, sku_id, available_units, expiry_date

routes.csv:
warehouse_id, store_id, unit_cost, capacity_units, lead_time_days, is_active

store inventory input:
store_id, sku_id, opening_units
```

Follow PRD for products/locations/config. Check negatives, duplicate keys,
orphan references, integer quantities, dates, active flags and missing fields.
Errors should identify file, row, column and rule; never silently repair input.
Route capacities are **shared across all SKUs/batches** on the route.

Normal should have ample eligible stock, scarce supply should constrain cover,
and expiry trap should include tempting cheap but unusable stock. Plant at least
one inactive-route, late-arrival and short-shelf-life option per scenario. Log
assumptions and seeds before looking at performance.

### Eligibility

Ship on planning-week Monday. A batch–store shipment option is allowed only if:

- Route active.
- Arrival after lead time is no later than day 2.
- Expiry minus arrival date is at least 3 days.

Count rejected batch–store options under `route`, `lead_time`, `shelf_life`.
Document whether counts overlap or use first-failure precedence.

### Optimization and whole units

For all six planning levels:

```text
target = max(0, ceil(forecast) - opening stock)
minimize freight + 12 * unmet target units

sum shipments from a batch <= batch stock
sum shipments on a route <= shared route capacity
shipments to each store–SKU + unmet = target
shipments >= 0; unmet >= 0
```

Build variables only for eligible options. Unmet absorbs shortages; report actual
solver status/time. Handle solver errors without presenting fabricated plans.
Floor shipments to whole units, recompute unmet/freight/objective, then check.
Do not label floored results proven integer-optimal.

### Independent checker (separate from solver)

No solver imports. Recheck from original inventory/routes/targets, not just
shipment display fields. Reject oversold batches, negative/fractional units,
inactive routes, late arrivals, short life on arrival, shared-capacity excess,
over-target shipments, and inconsistent unmet/cost totals.

Test each injected violation. Never set `checker.passed` from solver success.

### Two allocation baselines

Pro-rata and cheapest-eligible-first greedy, using identical stock, routes,
targets, eligibility and flooring. Store iteration for greedy is ID order.
All plans pass the same independent checker. Preserve the continuous LP objective
to test that it is no worse than each feasible baseline **before flooring**.
Do not assume it wins on realized cost.

## 9. Stream D — actual computed evaluation

For each scenario, evaluate fixed plans at all six levels and compare LP,
pro-rata and greedy. Use **the same 200 seeded draws** for compared plans.

Use the generator's planning-week hidden truth **only in the evaluator**, never
for forecasting, allocation targets, tuning or model selection. Its dispersion
is negative-binomial **size k**, not standard deviation. For mean μ and size k,
NumPy's parameterization uses `n=k`, `p=k/(k+μ)`.

For each store–SKU and draw:

```text
available = opening stock + shipped
short = max(0, demand - available)
excess = max(0, available - demand)
realized cost = freight + sum(12 * short) + sum(3 * excess)
fulfillment = sum(min(demand, available)) / sum(demand)
```

Report mean realized cost, freight, mean fulfillment, **P10 fulfillment** (10th
percentile across draws), and unmet target units. Keep simulated lost sales
distinct from unmet target units. Define zero-demand handling explicitly.

Risk Dial recommendation: cheapest mean-realized-cost plan meeting the user's
P10 threshold, or explicitly none. No monotonic fulfillment or LP win may be
hardcoded. Report ties/losses. Preserve shared draws and report seeds/provenance.

Expiry-risk proxy: unshipped units expiring within 7 days of week end; not actual
measured waste reduction. Forecast pinball/calibration should come from actual
holdout artifacts, including both methods where available, not demo placeholders.

## 10. Frontend already built — do not rewrite it

Streamlit + Plotly + pandas, maximum three pages:

1. Data & Validation: files/checks/warnings and forecast table/chart.
2. Plan & Export: levels, totals, blocked counts, shipments, unmet and CSV download.
3. Risk Dial & Baselines: threshold, recommendation, cost/service chart, comparisons,
   forecast quality and calibration.

App code never imports the engine or runs models/LP on clicks.

### Two isolated sources

```text
results/          # synthetic MOCK demo artifacts; never overwrite
engine_results/   # actual COMPUTED synthetic artifacts
```

UI selector: **Demo / Engine results**. Engine mode never falls back to demo.
Missing files show unavailable states. Preserve actual IDs, never substitute
mock IDs. Alias mapping is centralized:

| UI alias | Canonical backend directory |
|---|---|
| normal | normal |
| scarce | scarce_supply |
| expiry | expiry_trap |

Forecast viewing can work alone. Full planner is gated until all seven JSON
files parse and index acceptance flags are true. Failed-checker plans are hidden
and cannot be exported. The flags record acceptance; they do not execute checks.

## 11. Frontend artifact contract — exact essentials

Read the current frontend **`CONTRACT.md`**, **`engine_results/README.md`**, and
`app_lib/artifacts.py` before writing exports. Older handoffs mentioning replacing
`results/` have been superseded: computed files go to **`engine_results/`**.

Per canonical scenario:

```text
engine_results/<scenario>/
  meta.json
  validation.json
  forecast.json
  plan.json
  risk_dial.json
  baselines.json
  evaluation.json
```

The structures below are field specifications, not measured results. Export
native JSON numbers/booleans (not strings, NumPy scalars, NaN or infinity).

### meta.json

```text
scenario_id, scenario_name, planning_week, seed,
forecaster_used, forecaster_scores,
solver_status, solve_time_seconds,
levels: [P50,P60,P70,P80,P90,P95], default_level: P50,
network: {warehouses:3, stores:8, skus:5},
latest_arrival_day:2, min_shelf_life_days:3
```

UI currently recognizes forecaster names `baseline_ma4` and `ml_gbm`; map actual
`MA4` / `GB` to these at export, retaining original method names as provenance.
Solver status values: `optimal`, `feasible`, `infeasible`, `error`. Record each
level's actual status too if needed; do not hide mixed failures behind one badge.

### validation.json

```text
ok: boolean
files: [{name, rows, status, errors, warnings}]
checks: [{id, label, passed, detail}]
errors/warnings: [{file, row, column, rule, message}]
```

Reports must reflect checks actually executed. Blocking validation errors mean
no usable plan. Do not copy mock checks, especially leakage/model checks you
have not actually run or received from A.

### forecast.json (accepted normal already exists)

```text
rows: [{store_id, sku_id, opening_units,
        p50,p60,p70,p80,p90,p95,
        target_p50,target_p60,target_p70,target_p80,target_p90,target_p95}]
```

The app currently requires targets P50/P90; all six are supported. Keep the
accepted file intact unless a coordinated rerun is required.

### plan.json

```text
scenario_id
levels:
  P50:                        # same structure for all six levels
    shipments: [{warehouse_id,store_id,sku_id,batch_id,units,
                 unit_cost,freight,arrival_day,shelf_life_on_arrival,expiry_date}]
    unmet: [{store_id,sku_id,target_units,shipped_units,unmet_units}]
    blocked: {route, lead_time, shelf_life}
    totals: {target_units,shipped_units,unmet_units,freight,shipments}
    checker: {passed:boolean, violations:[]}
```

Use structured violation records where possible. `shipments` inside `totals`
is a count. Extra solver/objective/provenance fields are welcome if coordinated.

### risk_dial.json

```text
draws: 200
levels: [{level,freight,realized_cost_mean,realized_cost_p90,
          fulfillment_mean,fulfillment_p10,shipped_units,unmet_units}]
```

Six entries in P50–P95 order. Fulfillment stored as **fractions 0–1**, not 0–100.

### baselines.json

```text
levels: [P50]
methods: [{id,name,planned_objective,realized_cost_mean,
           fulfillment_mean,fulfillment_p10,freight,unmet_units,checker_passed}]
```

IDs: `lp`, `pro_rata`, `greedy`. Current UI displays one P50 comparison per
scenario. Compute all levels for fair evaluation; agree an additional envelope
with C before changing UI-facing `methods`. Never label P90 comparison as P50.

### evaluation.json

```text
pinball: {scored_weeks:"41-52",baseline_ma4,ml_gbm,selected}
calibration: [{level,nominal,observed,within_tolerance}]
expiry_risk_units
```

Map real backend calibration columns to these fields. Nominal/observed are
fractions. Tolerance is absolute gap <=0.10. Use selected model's actual holdout
coverage; retain both models' tables as extra data if desired. Do not invent
ML scores if ML was unavailable; coordinate null-safe display with C.

## 12. Joint activation gate — do not bypass

Only after complete normal run is checked jointly, frontend engine index may have:

```json
{
  "mock": false,
  "integration_validated": true,
  "scenarios": [
    {"id":"normal","name":"Normal"},
    {"id":"scarce_supply","name":"Scarce Supply"},
    {"id":"expiry_trap","name":"Expiry Trap"}
  ]
}
```

Do not add this just to unlock UI while B/D files are missing. No mixed mock
plans and computed forecasts. For partial work, keep gate off and view forecasts.

Current frontend gate is global plus per-scenario file existence; it is not a
complete schema/feasibility validator. Frontend's old `tests/test_contract.py`
checks **demo** files in `results/`, not arbitrary engine output. Its green suite
alone cannot certify B/D results. Add actual computed-artifact tests and run the
independent checker before joint acceptance.

## 13. Implementation sequence and tests

1. Pull current backend; run existing tests in its pinned environment.
2. Read PRD/contracts; inspect accepted forecast and stock in frontend repo.
3. Freeze supply schemas/assumptions with C. Build and validate normal inputs.
4. Implement eligibility, then a tiny hand-solvable LP and flooring.
5. Implement independent checker and injected-violation tests.
6. Implement both baselines; check feasibility and continuous LP objective bound.
7. Implement shared 200-draw evaluation and six-level Risk Dial.
8. Export complete normal artifacts; deliver to C for UI and contract validation.
9. Jointly accept normal, then extend supply scenarios and repeat comparisons.
10. Update README/handoff with real test output, commit hashes and limitations.

Required tests include seed reproducibility, row-level invalid input, ID/pair
matching, all eligibility rules, hand-computed optimum, shared route and batch
limits, whole-unit flooring, exact unmet identities, checker rejection of every
violation type, baseline feasibility, evaluation formulas, common draws,
zero-demand handling, six levels, export round-trip, and actual-artifact UI loading.

Do not add P1 extras (FEFO bonus, disruptions, bottlenecks, hindsight, uploads)
until the P0 pipeline works. No multi-week model, truck routing, ERP, dispatch,
uncertain lead times, or proven integer optimality is required.

## 14. How we collaborate from here

Rahul sends the app owner:

- Proposed schemas before breaking changes.
- A complete `engine_results/normal/` candidate when ready, plus relevant source
  inputs/run command, exact backend commit/dependency versions and passing tests.
- Actual solver statuses, checker reports, baseline results, seeds and measured
  evaluation output. Include ties/losses/calibration failures, not just wins.

The app owner will:

- Validate IDs/targets/contracts/provenance and exercise actual artifacts in UI.
- Keep mock demo available while backend work is incomplete.
- Fix frontend incompatibilities in coordination, without rewriting backend.
- Agree acceptance before activation, commit and push accepted integrations.

**Next concrete delivery: one checked normal shipment plan, then its computed
Risk Dial and comparisons. Forecasting is already complete.**
