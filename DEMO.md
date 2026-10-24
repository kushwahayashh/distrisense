# Demo Script — 3 minutes

**Setup before you start**

```bash
cd /home/eren/Travizthon
source .venv/bin/activate
streamlit run app.py
```

Open http://localhost:8501, pick **Normal** in the sidebar, stay on the default page.
Have a terminal tab open for the CSV export check.

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

> "Every input is validated before a plan is built. Six CSVs plus config. Bad data
> is never silently repaired — errors name the file, row, column and rule."

Point at:
- **0 errors**, a few **warnings** (short history series, expiring batch, inactive route).
- The check list: schema, no negatives, unique IDs, no orphans, dates, quantiles never cross, no leakage.
- The forecast chart: **P50 vs P90** per store. "This is a range, not one number."

One line: "The forecast uses only past weeks. We test that changing planning-week data cannot change it."

---

## 0:50 – 1:50 · Page 2: Plan & Export

Click **Plan & Export**. Level **P50**.

> "This is the actual recommendation: which batch leaves which warehouse, to which
> store, how many units, and when it arrives."

Point at the four numbers:
- **Freight**
- **Shipped units**
- **Unmet units** — "reported, not hidden"
- **Target units**

Point at the green banner:
> "The independent checker passed. It is a separate module with no solver imports.
> It rejects overselling, late arrival, short shelf life, over-capacity, and
> shipments above target. Nothing is shown or exported until it passes."

Point at **Options blocked by eligibility rules**:
- Route inactive
- Arrives too late
- Shelf life too short

> "These are options the optimizer was not even allowed to consider. A naive
> cheapest-first rule would have shipped them."

Switch scenario to **Expiry Trap**, stay on P50:
> "Same optimizer, same rules. Watch the shelf-life blocks jump. The cheapest
> warehouse holds stock that cannot arrive and still be sellable — so it is
> excluded, and unmet units appear instead of a bad shipment."

Click **Download plan CSV**.
> "The planner reviews and exports. The app does not dispatch trucks."

---

## 1:50 – 2:50 · Page 3: Risk Dial & Baselines

Switch back to **Normal**. Click **Risk Dial & Baselines**.

> "One demand number hides risk. So we run the same optimizer at six planning
> levels, P50 to P95, against the same 200 simulated demand outcomes."

Point at the chart and the cards:
- Slider at **90% P10 fulfillment**.
- The star marks the **cheapest plan that meets the threshold**.
- Say: "At 90%, it picks **P90** — the cheapest plan whose bad week still serves 90%."

Now switch to **Scarce Supply**:
> "Here, no level reaches 90%. The app says so. It does not round up or hide it."

Point at the table: freight rises with the level; fulfillment rises too.
> "This is the measured cost of reliability on this scenario — not a guarantee."

Scroll to **Baselines**:
> "The LP is compared against pro-rata and cheapest-first greedy on identical
> inputs. The LP minimizes the planning objective, not realized cost — so it can
> tie or lose. We show the result either way."

Scroll to **Forecast quality**:
> "The ML model only ships if it beats the four-week moving average on pinball
> loss. Here it did / did not, so we used the baseline / the ML model. No claim
> beyond the measured score."

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

**"Is the plan optimal?"**
The LP is optimal in continuous units. We floor to whole units, so the exported plan is feasible but not proven optimal in whole units. We say that explicitly.

**"Did the ML model win?"**
Check the Forecast quality card. We report the pinball score for both and use the lower one. If the baseline won, we say the baseline won.

**"Why synthetic data?"**
The problem statement allows it. We plant the traps deliberately — scarce supply, expiring cheap stock, inactive routes — so the constraint logic is testable. We do not claim real-world performance.

**"What happens if a warehouse goes down?"**
That is a P1 disruption toggle. Not in this build. We would re-optimize with the same inputs and compare against the repaired old plan.

**"How do you know the checker is independent?"**
Separate module, no solver imports, and injected-violation tests — each violation type must fail the check.

---

## Do not say

- "Our AI predicts demand perfectly."
- "This saves X%."
- "P90 means 90% service."
- "The plan is optimal."
- "We reduce waste."

Say what is measured, and say what is not.
