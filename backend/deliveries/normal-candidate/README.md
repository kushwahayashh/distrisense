# Normal candidate — partner review

**Delivery-time status: computed synthetic backend candidate, not yet activated.**
This candidate was subsequently reviewed and activated in the frontend; the
acceptance record is `engine_results/index.json` in the app repository. The text
below is preserved as the original review request.

Implementation commit: `a22e7cd` (full hash in `normal/audit/provenance.json`).
The later delivery commit packages artifacts; it does not change engine code.
The provenance's working-tree entries refer to pre-existing, excluded local
files, not unpublished changes to the engine. Every `src/*.py` hash is included.

`frozen-code/src/` is a byte-for-byte snapshot of the code that produced this
delivery (accepted head `75b1a6c`). It is kept so the verifier can still check the
original hashes after the active `src/planner.py` was generalized to all three
scenarios. The active code is checked separately with `--rebuild`.

## What to review

`normal/` has the seven JSON files required by the frontend contract. Transfer
those files to a **review copy** of frontend `engine_results/normal/`; compare
its existing accepted forecast before replacing anything. Do not copy `audit/`
or `inputs/` into the UI, overwrite mock `results/`, or enable the activation
index until joint acceptance. Frontend readiness/rendering is still unverified.

`normal/audit/` includes supply/stock, all 18 independently checked plans,
all-level baseline comparisons, common draws and provenance. `inputs/` freezes
the source data and saved forecast/holdout outputs, including the original
accepted forecast. Hidden truth is an **evaluator-only** input. No forecast was
rerun for this delivery. Absolute source paths in provenance describe the
original run; corresponding portable snapshots are under `inputs/`.

## Verify from the repository root

Use the backend's pinned environment, separately from the frontend environment:

```bash
python -m pytest -q
python deliveries/normal-candidate/verify.py
python deliveries/normal-candidate/verify.py --rebuild
```

The default run checks the frozen code snapshot and source hashes, then rechecks
all 18 plans, the shared draws and the Risk Dial with the current independent
checker. `--rebuild` additionally rebuilds the candidate with the current
scenario-parameterized planner and asserts that all seven artifacts are identical
apart from solver timings.

`verification/` records the actual backend test and candidate-audit output.
Run versions: Python 3.14.4, NumPy 2.4.4, pandas 3.0.2, scikit-learn 1.8.0,
SciPy 1.17.1. Use `requirements.txt`; versions/seed alone do not prove artifact
equivalence, so the verifier checks hashes and recomputes evaluations too.

To rebuild from the frozen inputs without forecasting or overwriting artifacts:

```bash
python - <<'PY'
from pathlib import Path
from src.planner import build_candidate
root = Path('deliveries/normal-candidate/inputs')
print(build_candidate(
    Path('candidate_engine_results/partner-review'),
    data_dir=root / 'data/normal',
    output_dir=root / 'outputs/normal',
    accepted_forecast=root / 'engine_results/normal/forecast.json',
))
PY
```

The destination must not already exist. Solver runtimes and provenance paths
will naturally differ; supply, demand draws and numerical results should agree.

## Measured results and acceptance checklist

- All six LP levels optimal; all 18 method/level plans pass the checker.
- P50: 1,577 target/shipped units, zero unmet target units, ₹4,027 freight.
- P50 mean simulated cost: LP **₹8,168.965**, greedy **₹8,168.965** (tie),
  pro-rata **₹10,135.465**. No general LP-win claim.
- Default 0.90 P10 threshold selects **P80**: P10 fulfillment approximately
  0.91496, mean simulated cost ₹8,362.64.
- All comparisons share the same 200 seeded draws. Fractions are 0–1.
- Check frontend JSON loading, all six levels, correct IDs/targets, shipment
  display/CSV round-trip, P50 comparison labels, and Risk Dial recommendation.
- Report incompatibilities before activation. The backend suite is not frontend
  certification. Full scarce/expiry exports remain deferred until normal acceptance.

Synthetic, single-week prototype only. Unmet target units are not simulated lost
sales; floored plans are not proven integer-optimal; expiry risk is not measured waste.
