# Scarce Supply and Expiry Trap — Stream C review

Backend branch: `feat/scarce-expiry`

Implementation commit: `e94e05f19bea4c19a6f944c5675e0893ac374c58`

Delivery commit: `a514233ebf349f71b85831e3fba77d5232f082ea`

Delivery package: `deliveries/scarce-expiry-candidates/` in the backend repository.

## What was verified

### Backend

- **166 backend tests pass** (`verification/pytest.txt`).
- The standalone verifier rechecks **18 plans per scenario** (six levels × LP,
  pro-rata and greedy), regenerates supply, reproduces the shared **200 × 40**
  demand matrix, verifies source/code hashes, LP continuous bounds, P50 baseline
  comparisons and the Risk Dial result.
- Both scenarios report every solver status as `optimal`.
- Scarce Supply: 1,050 available units, route capacity 120. P50 ships 969 of
  1,577 target units; 608 are unmet. No level reaches the default 90% P10
  threshold, so `recommended_level` is `null`.
- Expiry Trap: all `W01` batches expire after 2 days and are excluded; shelf-life
  blocks rise from 7 (Normal) to 70. P50 still covers all 1,577 target units at
  ₹4,609 freight. At 90% P10, **P80** is the cheapest qualifying level.

### Frontend

The seven computed files for each scenario are installed under
`engine_results/scarce_supply/` and `engine_results/expiry_trap/`. The accepted
Normal forecast, opening stock, mock `results/`, and backend artifacts were not
modified.

- **67 frontend tests pass**, including 11 new computed-artifact tests.
- All three pages render for both scenarios in an isolated activated copy.
- All six levels display only after `checker.passed` is true.
- Shipment CSV serialization/reimport preserves values.
- Scarce Supply shows the unmet table and the “no level reaches” Risk Dial state.
- Expiry Trap shows the 70 shelf-life blocks and recommends **P80** at 90%.
- Expiry Trap's P50 LP and greedy tie; pro-rata is worse and leaves 33 units unmet.
- Injecting a checker failure hides shipments and disables export.

## Measured synthetic results

| Scenario | P50 target / shipped / unmet | P50 freight | P50 mean realized cost | P10 | Recommendation at 90% |
|---|---:|---:|---:|---:|---|
| Scarce Supply | 1,577 / 969 / 608 | ₹2,344 | ₹12,288.64 | 56.57% | None |
| Expiry Trap | 1,577 / 1,577 / 0 | ₹4,609 | ₹8,750.97 | 82.10% | P80 |

Scarce Supply P50 baselines: LP ₹12,288.64, greedy ₹12,963.67, pro-rata
₹13,196.02. Expiry Trap P50 baselines: LP and greedy tie at ₹8,750.97; pro-rata
₹10,461.49 with 33 unmet units. These are synthetic, single-week results and imply
no real-world savings.

## Acceptance note

The backend owner was unavailable when this delivery was completed. The app owner
reviewed the independent verifier output, ran the full frontend suite, and accepted
both scenarios for this build. This is **single-owner acceptance**, not a claim of
joint sign-off by both original owners. The evidence and commit hashes are recorded
in `engine_results/index.json`; Normal's earlier joint acceptance is unchanged.

## Remaining work

1. Manual visual click-through of both scenarios in the running app.
2. Update the demo script/rehearsal to use all three computed scenarios.
3. Final README/submission polish and backup recording.
