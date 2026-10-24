# DistriSense — Adaptive Distribution Intelligence

**Team Byte Works** · Triwizathon 2026 · Problem Statement 2

Weekly FMCG replenishment planner. For each store × SKU it recommends which
warehouse batch to ship, how many units, and from where — and refuses any
shipment that would arrive late or with too little shelf life left.

This repository contains the **Streamlit app**, a separate mock demo, and the
accepted computed **Normal** scenario in `engine_results/normal/`. Forecasting,
optimization and evaluation live in the [backend repository](https://github.com/rahullamani01/engine-module-).
Choose **Engine results → Normal** to view the verified delivery plans and Risk
Dial. Computed Scarce Supply and Expiry Trap deliveries are still pending.

> ⚠️ All numbers in `results/` are synthetic mock data for UI development.
> They are not engine results and must not be presented as such.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/make_mock_results.py     # mock artifacts (skip once the engine writes results/)
streamlit run app.py
```

Open http://localhost:8501.

## Pages (3, per the PRD)

| Page | What it shows |
|---|---|
| **Data & Validation** | Files checked, row counts, pass/fail checks, warnings, forecast vs. store stock |
| **Plan & Export** | Shipment table per planning level, blocked-option counts, unmet units, checker status, CSV export |
| **Risk Dial & Baselines** | Cost vs. P10 service across 6 levels, cheapest qualifying plan, LP vs. two baselines, pinball loss and calibration |

## Structure

```
app.py                     entry point (st.navigation)
app_lib/artifacts.py       reads results/*.json — no engine imports
app_lib/ui.py              shared styling, sidebar, cards
app_pages/                 the three pages
scripts/make_mock_results.py   deterministic mock artifacts (seed 42)
results/                   engine → app contract (see CONTRACT.md)
CONTRACT.md                exact JSON schemas and invariants
```

## Engine integration

**Updated integration:** use the sidebar's **Demo / Engine results** selector.
Demo reads `results/`; engine mode reads **`engine_results/`** with canonical
scenario folders `normal`, `scarce_supply`, and `expiry_trap`. There is no fallback
between the two sources. See [engine_results/README.md](engine_results/README.md)
for partial forecast delivery and the joint full-planner acceptance gate.

The original handoff instructions below describe the artifact shapes; deliver
computed artifacts to `engine_results/` instead of overwriting the demo.

The app never imports the engine. It only reads `results/`.

1. Engine writes `results/<scenario>/{meta,validation,forecast,plan,risk_dial,baselines,evaluation}.json`.
2. Engine writes `results/index.json`.
3. Restart the app.

Schemas and invariants are in [CONTRACT.md](CONTRACT.md). The key rule: a plan is
displayed or exported **only** when `checker.passed` is `true`.

## Honest framing

- A planning level is a setting, not a fulfillment guarantee.
- The LP minimizes the planning objective, not realized cost; it can tie or lose to a baseline.
- Whole-unit plans are floored after the LP and are not proven optimal in whole units.
- The ML forecaster ships only if it beats the baseline on held-out pinball loss; otherwise the baseline ships and no ML claim is made.
- The app shows ties and losses; it does not promise savings.

## Scope

P0 only. No truck routing, live dispatch, ERP/POS integration, store transfers,
multi-week inventory, or lead-time uncertainty.
