# Backend snapshot — DistriSense engine

This directory is a **plain-folder snapshot** of the standalone engine repository,
copied from tracked files at a single commit. It is not a git subtree and shares
no history with the app repository. From now on, this is the active engine source.

| Field | Value |
|---|---|
| Source repository | `https://github.com/rahullamani01/engine-module-` |
| Snapshot commit | `3eafc66a36606dfa7fcb1528550847a865a52644` (merge of PR #2) |
| Snapshot method | `git archive` of the commit, extracted here |
| Source repo status | **Frozen.** Do not push engine changes there again. |
| Active copy | This `backend/` directory in the central `distrisense` repo |

The standalone repository is left online as read-only history. It is not deleted;
archiving it on GitHub is the final cleanup step. If a change is ever needed in
both places, treat this directory as canonical and the old repo as an archive.

## Why a folder snapshot

The app and engine have unrelated git histories and different layouts. A merge or
subtree would rewrite paths and risk breaking a working demo. A snapshot keeps the
engine runnable from `backend/` with zero path surgery, while the app keeps reading
only `engine_results/`. Cleanup of duplicated or historical files is deliberately
deferred until after submission.

## What is included

```
backend/
  src/                      engine source (forecasting, supply, LP, checker, evaluation)
  tests/                    backend test suite
  deliveries/               frozen candidate deliveries + independent verifiers
    normal-candidate/       accepted Normal delivery (includes frozen-code/)
    scarce-expiry-candidates/  Scarce Supply and Expiry Trap deliveries
  engine_results/normal/    original accepted forecast artifact
  README.md                 original engine README
  requirements.txt
  pytest.ini
```

Excluded from the snapshot: `.git`, virtual environments, `__pycache__`,
`.pytest_cache`, generated `data/`, `outputs/`, and `candidate_engine_results/`.
All inputs needed to verify the deliveries are frozen inside each delivery's
`inputs/` directory, so no ignored local files are required.

## Environments

Keep the two environments separate. The app uses the repository-root `.venv`; the
engine uses its own environment, because their dependency pins differ.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The original accepted runs recorded Python 3.14.4, NumPy 2.4.4, pandas 3.0.2,
SciPy 1.17.1 and scikit-learn 1.8.0. Exact versions and seed alone do not prove
artifact equivalence; the verifiers check hashes and recompute evaluations.

## Tests and verification

Run from `backend/` with the engine environment:

```bash
python -m pytest -q

python deliveries/normal-candidate/verify.py
python deliveries/normal-candidate/verify.py --rebuild

python deliveries/scarce-expiry-candidates/verify.py scarce_supply
python deliveries/scarce-expiry-candidates/verify.py expiry_trap
```

Recorded result at snapshot time:

- `pytest`: **166 passed**
- Normal verifier: 18 plans, shared 200 × 40 draws, frozen code and source hashes
- Normal `--rebuild`: all seven artifacts identical to the accepted delivery
  apart from solver timings
- Scarce Supply verifier: PASS
- Expiry Trap verifier: PASS

Each verifier is independent of the solver: it rechecks every level and baseline
plan against the original batches, routes and targets, regenerates supply,
reproduces the shared demand draws and every reported evaluation, and confirms the
LP continuous bound and Risk Dial result. A plan is never shown or exported unless
`checker.passed` is true.

### Normal verifier and `frozen-code/`

The Normal delivery was produced at accepted head `75b1a6c`. The active
`src/planner.py` was later generalized to accept `normal`, `scarce_supply` and
`expiry_trap` while defaulting to `normal`. Because the delivery's provenance pins
the original code hash, the delivery keeps a byte-for-byte copy of the producing
code in `deliveries/normal-candidate/frozen-code/src/`; the default verifier
checks that snapshot. `--rebuild` then proves the current planner reproduces all
seven artifacts identically (solver timings excluded). This preserves the original
evidence instead of weakening the hash check.

## Data boundary

- `backend/` never writes into the app's `results/` or `engine_results/`.
- The app never imports `backend/`.
- `engine_results/` is the only hand-off boundary; it contains accepted, computed
  artifacts and the activation index.
- Demo `results/` stays separate and must never be presented as engine output.
- All data is synthetic. Results imply no real-world accuracy or savings.

## Cleanup deferred

Do not remove duplicates yet. Known items for the post-submission pass:

- the original standalone repository (archive, do not delete);
- historical `deliveries/` review text that describes pre-acceptance status;
- stale root-level handoff documents superseded by `RAHUL_HANDOFF.md`;
- generated local `data/`, `outputs/` and candidate directories, if recreated.
