# Message to send your engine partner

Copy everything below the line into WhatsApp / Discord / email.

---

Hey — quick update. I've built the Streamlit app and a mock data generator. The app **never imports your code** — it only reads JSON files from `results/`. So you can build the engine independently and just drop the output in.

I'm sending you a zip (`distrisense-engine-handoff.zip`). Unzip it, then:

1. Read **`CONTRACT.md`** — exact schema for every file.
2. Look at **`results/normal/`** — a complete, correctly-shaped example.
3. Write your engine to produce the same 7 files for each scenario.

**Scenarios (exact ids):** `normal`, `scarce`, `expiry`

**Files per scenario:**

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

Plus `results/index.json` listing all three. In that file set `"mock": false` so the app stops showing the mock-data warning.

**Non-negotiables**

- `plan.json` must contain all six levels: `P50, P60, P70, P80, P90, P95`.
- `checker.passed` must be `true` only if the plan is genuinely valid — the app blocks CSV export otherwise.
- Forecast quantiles must be non-decreasing and never negative.
- `target = max(0, ceil(forecast) - opening_stock)`.
- `blocked` must count rejected options per rule: `route`, `lead_time`, `shelf_life`.
- `solver_status` is shown verbatim — never hide a non-optimal status.
- Validation errors mean **no plan**. Don't silently repair bad data.

**Priority order**

1. **By hour 7 (G1):** baseline MA4 + residual quantiles → eligibility → LP → checker → one full plan for `normal`. That's the integration milestone.
2. **By hour 11 (G2):** all three scenarios, Risk Dial, two baselines. ML only if it beats the baseline on pinball loss.
3. Don't wait for the ML model to start the pipeline. Baseline first, always.

**How to check your output**

```bash
pip install -r requirements.txt
pytest -q                 # 8 contract tests
streamlit run app.py
```

If the tests pass and the app loads, the integration is done.

**One rule:** if you need to change a field name or add a field, tell me first — I'll update the app and the tests. Don't change the contract silently.

**First thing I need:** a real `results/normal/` folder, even with rough numbers. That's the moment our halves connect.
