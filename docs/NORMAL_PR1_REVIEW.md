# Normal candidate — Stream C review

Backend PR: https://github.com/rahullamani01/engine-module-/pull/1  
Reviewed head: `75b1a6cdb5ddb649262e405f347034ac8f133832`  
Artifact delivery commit: `146d63dfb466746a2dccbc3578759987aaff1724`  
Implementation: `a22e7cde7bd837019d33b46601573d6e2a396604`

## Frontend integration

The six missing computed artifacts have been copied to `engine_results/normal/`.
The existing accepted `forecast.json` was compared for exact JSON equality and
left untouched. Opening stock matches the committed CSV. Mock `results/` files
were not modified.

Following this review, the app owner explicitly authorized merging backend PR #1
and activating **Normal only**. `engine_results/index.json` records acceptance.
Delivery metadata remains unchanged, including its original pending-acceptance
marker; the index records the later decision. Scarce/expiry remain unaccepted.

Backend merge commit: `f61c73d174be557953dd5e60da1e796f8ad3384f`.
Post-activation frontend suite: **56 tests pass**, including checks that only
explicitly accepted scenarios can activate. The original review run was 54 tests.

### What passed

- **54 frontend tests**, including actual computed-artifact tests.
- All three pages run without exceptions in an isolated activated review copy.
- All six planning levels display independently checked shipment plans.
- CSV serialization/reimport preserves shipment values.
- Separate backend check: **18/18 reimported CSV plans** pass the independent
  checker against original batch, route and target data (six levels × three methods).
- Failed checker hides shipment controls; unmet table hides fully covered pairs.
- P50 baseline labels are explicit; LP and greedy ties remain visible.
- At the default 90% P10 threshold, both table and recommendation select **P80**.
- At a 100% threshold, UI honestly reports no qualifying plan.
- Backend delivery verifier reproduces all 18 plans' evaluations, common
  **200 × 40** demand matrix, code/source hashes, LP bounds and recommendations.

These are automated rendering checks, not a manual visual inspection or a
full three-scenario acceptance. Backend code stays in its own pinned environment.

## Measured synthetic normal results

| Item | Result |
|---|---:|
| P50 target / shipped | 1,577 / 1,577 units |
| P50 unmet target | 0 units |
| P50 freight | ₹4,027 |
| P50 LP mean realized cost | ₹8,168.965 |
| P50 greedy mean realized cost | ₹8,168.965 (tie) |
| P50 pro-rata mean realized cost | ₹10,135.465 |
| Default threshold recommendation | P80 |
| P80 P10 fulfillment | 91.4963% |
| P80 mean realized cost | ₹8,362.64 |

Zero unmet **target** units does not mean zero realized lost sales. The app keeps
the planning target and simulated evaluation separate. No real-world claims.

## Backend test portability issue

On a clean PR checkout, the first backend run produced **154 passed, 8 setup
errors**, because `tests/test_targets.py` calls `load_forecast("normal")` with
its default ignored `outputs/` directory. That file is not part of a clean checkout.
This does not invalidate the packaged delivery: its standalone verifier passed.

A minimal test-only correction is prepared in
`docs/normal-pr1-target-fixture.patch`. It loads the committed frozen normal
forecast under `deliveries/normal-candidate/inputs/outputs/` explicitly, without
training a model or depending on untracked local state. Engine source/provenance
hashes are unchanged. Apply to the backend PR branch and rerun its suite.

With this test-only fix applied locally, the full backend rerun produced
**162 passed in 38.03 seconds**, and the standalone verifier passed again.
This is independent review output, not the original reported 20.81-second run.
Rahul subsequently pushed an equivalent fixture fix in `75b1a6c`. Stream C
checked that commit in a new clean worktree and independently reran the suite:
**162 passed in 37.89 seconds**. The standalone delivery verifier also passed.
Only `tests/test_targets.py` changed; engine source and delivery artifacts remain
unchanged. The prepared patch is now historical reference; do not reapply it.

## Next actions

1. **Done:** Rahul pushed the target-test fixture fix; backend tests and delivery
   verification pass independently on the pushed version.
2. **Done:** app owner reviewed the result and explicitly authorized acceptance.
3. **Done:** PR approved/merged; Normal activation recorded in the frontend index.
4. Rahul extends complete candidate exports to `scarce_supply` and `expiry_trap`.
5. Stream C repeats artifact, rendering, CSV and recommendation checks per scenario.

The current PR packages audit evidence and frozen evaluator inputs in its own
repository. Those large audit/truth files are deliberately not copied into the
frontend; follow the pinned PR delivery for independent recomputation.
