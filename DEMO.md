# Demo Script — 3 minutes

**Setup before you start**

```bash
cd /home/eren/Travizthon/distrisense
source .venv/bin/activate
streamlit run app.py
```

Open http://localhost:8501. In the sidebar choose **Engine results → Normal**.
That is the computed, independently checked candidate. Keep a terminal tab open
for the CSV export check.

> If you switch to **Demo**, everything is mock UI data. Say so. The computed
> Scarce Supply and Expiry Trap deliveries are still pending; do not present the
> mock versions as engine results.

---

## 0:00 – 0:20 · The problem

> "FMCG companies split limited warehouse stock across stores every week. Send too
> little and you lose sales. Send too much and it expires. Send from the wrong
> warehouse and freight eats the margin. Today most teams use a fixed rule and a
> single demand number. We built a planner that respects expiry, lead time and
> route capacity — and shows what extra reliability actually costs."

Do **not** open with "we used machine learning." Open with the decision.

---

## 0:20 – 0:50 · Page 1: Data & Validation

Click **Data & Validation**.

> "Every input is validated before a plan is built. Bad data is never silently
> repaired — errors name the file, row, column and rule."

Point at:
- **0 errors, 0 warnings** in this frozen Normal candidate.
- Five validated inputs: locations, products, opening stock, inventory batches,
  routes.
- The check list: supply references, accepted forecast and stock match, all six
  plans independently checked, continuous LP bound.
- The forecast chart: **P50 vs P90** per store. "This is a range, not one number."

One line: "The forecast uses only past weeks. The accepted forecast was not refit
when the planner ran; the adapter reran it without fitting and matched all six
targets."

---

## 0:50 – 1:50 · Page 2: Plan & Export

Click **Plan & Export**. Level **P50**.

> "This is the actual recommendation: which batch leaves which warehouse, to which
> store, how many units, and when it arrives."

Point at the four numbers:
- **Freight ₹4,027**
- **Shipped units 1,577**
- **Unmet units 0** — "reported, not hidden"
- **Target units 1,577**

Point at the green banner:
> "The independent checker passed. It is a separate module with no solver imports.
> It rejects overselling, late arrival, short shelf life, over-capacity, and
> shipments above target. Nothing is shown or exported until it passes."

Point at **Options blocked by eligibility rules**:
- Route inactive: **10**
- Arrives too late: **10**
- Shelf life too short: **7**

> "These are options the optimizer was not even allowed to consider. A naive
> cheapest-first rule would have shipped them."

Switch the level to **P95**:
- Freight rises to **₹6,967**; shipped units to **2,743**; target units **2,743**.
> "Higher planning levels ship more and cost more. The checker passes at every
> level; the plan is feasible, not proven optimal in whole units."

Click **Download plan CSV**.
> "The planner reviews and exports. The app does not dispatch trucks."

Optional honest note:
> "Scarce Supply and Expiry Trap computed plans are not in this build yet. Their
> demo screens are mock data, clearly labelled. We are not claiming otherwise."

---

## 1:50 – 2:50 · Page 3: Risk Dial & Baselines

Click **Risk Dial & Baselines**.

> "One demand number hides risk. So we run the same optimizer at six planning
> levels, P50 to P95, against the same 200 simulated demand outcomes."

Point at the chart and the cards:
- Slider at **90% P10 fulfillment**.
- The star marks the **cheapest plan that meets the threshold**.
- Say: "At 90%, it picks **P80** — the cheapest plan whose bad week still serves
  about 91.5%."
- P80 mean realized cost is **₹8,362.64**; P50 is **₹8,168.97** but only
  **82.1%** P10 fulfillment.

Point at the table: freight rises with the level; fulfillment rises too.
> "This is the measured cost of reliability on this scenario — not a guarantee."

Scroll to **Baselines**:
> "At P50, the LP and cheapest-eligible greedy tie at ₹8,168.97 mean realized
> cost. Pro-rata costs ₹10,135.47 and leaves 33 target units unmet. We show the
> tie instead of pretending the optimizer won."

Scroll to **Forecast quality**:
> "The ML model only ships if it beats the four-week moving average on pinball
> loss. Here GBM scored 4.711 versus 4.934 for the baseline, so GBM was used. No
> claim beyond the measured score."

Move the threshold slider to **100%**:
> "No level reaches it. The app says so. It does not round up or hide it."

---

## 2:50 – 3:00 · The honest close

> "Three things make this different: hard expiry and lead-time eligibility, a
> priced risk dial, and independent verification. We are not claiming real-world
> savings or that the plan is optimal in whole units. We are claiming the plans
> respect the rules, and that the trade-off is measured."

Stop talking. Let the judges ask.

---

## Likely questions

**"Is P90 a 90% fulfillment guarantee?"**
No. It is a planning level — how much demand we plan for. Actual fulfillment is measured separately against 200 draws and shown as mean and P10.

**"Why does 90% P10 choose P80, not P90?"**
Because P80 is the cheapest plan whose 10th-percentile fulfillment still clears
90% (91.5%). P90 clears it too, but costs more. The rule is cheapest qualifying,
not highest level.

**"Is the plan optimal?"**
The LP is optimal in continuous units. We floor to whole units, so the exported plan is feasible but not proven optimal in whole units. We say that explicitly.

**"Did the ML model win?"**
Check the Forecast quality card. We report the pinball score for both and use the lower one. Here GBM won. If the baseline won on another run, we would say so.

**"Why synthetic data?"**
The problem statement allows it. We plant the traps deliberately — scarce supply, expiring cheap stock, inactive routes — so the constraint logic is testable. We do not claim real-world performance.

**"Where are the other two scenarios?"**
Normal is fully computed and accepted. Scarce Supply and Expiry Trap have
backend supply logic but their complete checked deliveries are still pending, so
the app does not activate them. The Demo source shows labelled mock screens only.

**"What happens if a warehouse goes down?"**
That is a P1 disruption toggle. Not in this build. We would re-optimize with the same inputs and compare against the repaired old plan.

**"How do you know the checker is independent?"**
Separate module, no solver imports, and injected-violation tests — each violation type must fail the check. We also reimported all 18 exported plans and reran the checker.

---

## Do not say

- "Our AI predicts demand perfectly."
- "This saves X%."
- "P90 means 90% service."
- "The plan is optimal."
- "We reduce waste."
- "All three scenarios are computed."

Say what is measured, and say what is not.
