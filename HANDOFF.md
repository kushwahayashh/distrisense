# Engine Handoff — DistriSense

> **SUPERSEDED.** This file describes an earlier two-repository state. Read
> [`RAHUL_HANDOFF.md`](RAHUL_HANDOFF.md) instead. Kept for history; cleanup is
> deferred until after submission.

**Product:** DistriSense · **Team:** Byte Works
**For:** the forecasting + optimization engine owner
**From:** the app owner
**Status:** the Streamlit app is built and running against mock artifacts.

---

## 1. The split

The app and the engine are fully decoupled.

- The app **never imports** engine code.
- The engine **never imports** app code.
- The only connection is the JSON files in `results/`.

This is deliberate: a broken model cannot break the demo, and the UI can be built
in parallel. Write files; the app picks them up on restart.

---

## 2. What exists already

| Path | What it is |
|---|---|
| `app.py` + `app_pages/` | the 3-page Streamlit app (done) |
| `CONTRACT.md` | exact JSON schemas and invariants (read this first) |
| `results/` | mock artifacts for `normal`, `scarce`, `expiry` |
| `scripts/make_mock_results.py` | regenerates the mock artifacts (seed 42) |
| `tests/test_contract.py` | 8 tests that validate any engine output |
| `requirements.txt` | dependencies |

The app currently displays **mock data**. The sidebar says so. Your job is to
replace it with real engine output.

---

## 3. What the engine must write

For **each** scenario id — exactly `normal`, `scarce`, `expiry`:

```
results/<scenario>/
  meta.json
  validation.json
  forecast.json
  plan.json
  risk_dial.json
  baselines.json
  evaluation.json
```

Plus:

```
results/index.json
```

with:

```json
{
  "generated_at": "2026-10-24T18:00:00",
  "mock": false,
  "scenarios": [
    { "id": "normal", "name": "Normal", "path": "results/normal" },
    { "id": "scarce", "name": "Scarce Supply", "path": "results/scarce" },
    { "id": "expiry", "name": "Expiry Trap", "path": "results/expiry" }
  ]
}
```

`"mock": false` removes the app's mock-data warning. Do not forget it.

A complete, correctly-shaped example is in `results/normal/`. Match its keys.

---

## 4. Non-negotiable rules

The app trusts these. Breaking them breaks the demo.

1. **All six levels** must exist in `plan.json`:
   `P50, P60, P70, P80, P90, P95`.
2. **`checker.passed`** must be `true` only if the plan is genuinely valid.
   The app disables CSV export when it is `false`.
3. **Forecast quantiles** must be non-decreasing and never negative.
4. **Targets** = `max(0, ceil(forecast) - opening_stock)`.
5. **`blocked`** must count rejected batch–store options per rule:
   `route`, `lead_time`, `shelf_life`.
6. **`solver_status`** is shown verbatim. Never hide a non-optimal status.
7. **Validation errors mean no plan.** Bad data is never silently repaired.
8. **Eligibility is hard**: active route, arrival ≤ day 2, ≥ 3 days shelf life on
   arrival. No expired or late shipment may appear in any plan.

---

## 5. Build order (matches the PRD gates)

| Gate | Hour | Must work |
|---|---|---|
| G1 | 7 | Baseline MA4 + residual quantiles → targets/eligibility → LP → checker → **one full plan for `normal`** |
| G2 | 11 | All 3 scenarios, Risk Dial, 2 baselines, ML in or baseline-only confirmed |
| G3 | 14 | Feature freeze |

Rules:

- **Baseline forecaster first.** It ships if the ML model is late or loses.
- **Do not wait for the ML model** to start the pipeline.
- ML ships only if it has the lower pinball loss on weeks 41–52. Otherwise the
  baseline ships and no ML claim is made.
- The Risk Dial is the same LP run at six levels against the same 200 seeded draws.

---

## 6. Definition of done

- [ ] `results/index.json` has `"mock": false` and all 3 scenarios.
- [ ] Each scenario has all 7 files.
- [ ] `pytest -q` passes (8 contract tests).
- [ ] `streamlit run app.py` loads with no errors.
- [ ] Plan page shows 0 checker violations and the export button is enabled.
- [ ] Risk Dial shows 6 levels and highlights the cheapest qualifying plan (or
      honestly says none meets the threshold).
- [ ] No mock numbers remain in the demo path.

---

## 7. How to validate your output

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pytest -q                 # contract tests
streamlit run app.py      # visual check
```

The tests check the **contract**, not your model's quality. A passing test means
the app can render your output safely.

---

## 8. Changing the contract

If you need a field renamed, added or removed:

1. Message the app owner **before** changing it.
2. The app and `tests/test_contract.py` must be updated together.

A silent field change will blank a page or fail the checker. Coordinate first.

---

## 9. Honest framing (do not lose this)

The PRD's credibility rests on these statements:

- A planning level is a **setting**, not a fulfillment guarantee.
- The LP minimizes the **planning objective**, not realized cost. It can tie or
  lose to a baseline; report it either way.
- Whole-unit plans are **floored**, not proven optimal.
- Short-life and late stock is never shipped — that is enforced, not claimed.
- We do **not** claim actual waste reduction, real-world savings, or forecast
  accuracy on real data.

Keep `solver_status`, `checker.violations`, pinball scores and calibration honest.
The app displays them exactly as written.

---

## 10. First milestone — what to send back

Send a real `results/normal/` folder, even with rough numbers. That is the moment
the engine and app connect. Everything else comes after.
