# Rahul — DistriSense handoff

**Team Byte Works · Triwizathon 2026 · Problem Statement 2**
**Written:** 25 October 2026
**Current app commit:** `26db708`
**App running at:** http://localhost:8501

This supersedes `RAHUL_NEW_CHAT_HANDOFF.md` and the old root `HANDOFF.md`.
Read this file first, then `DEMO.md` before presenting.

---

## 1. Read this first: the repository changed

The engine now lives **inside the app repository**:

```
distrisense/                 ← the only repo you need
  app.py, app_lib/, app_pages/, tests/
  results/                   mock demo data — never present as engine output
  engine_results/            accepted computed artifacts + activation index
  backend/                   frozen engine snapshot, now the active engine source
    src/, tests/, deliveries/, SNAPSHOT.md
  DEMO.md
  RAHUL_HANDOFF.md           ← this file
```

**The old standalone repo `rahullamani01/engine-module-` is frozen at `3eafc66`.**
Do not push engine changes there again. The copy in `backend/` is canonical from
now on. The old repo is left online as read-only history and should be archived
after submission — not deleted.

This is a plain folder snapshot, not a git subtree. It has no shared history with
the app repo, which is intentional: nothing about the app's imports or paths
changed.

Full details: [`backend/SNAPSHOT.md`](backend/SNAPSHOT.md).

---

## 2. What is actually done

All three synthetic scenarios are computed, verified, and active in the app.

| Area | State | Evidence |
|---|---|---|
| Stream A forecasting | Complete | Backend tests; accepted forecast |
| Normal planner + Risk Dial | Complete, accepted, active | PR #1: artifacts `146d63d`, code `75b1a6c`, merge `f61c73d` |
| Scarce Supply | Complete, active | PR #2: impl `e94e05f`, delivery `a514233`, merge `3eafc66` |
| Expiry Trap | Complete, active | Same PR #2 |
| Frontend activation | Complete | `engine_results/index.json`, app commit `c30ec87` |
| Backend snapshot | Complete | This repo at `26db708` |
| Frontend tests | **67 pass** | `.venv/bin/python -m pytest` |
| Backend tests | **166 pass** | `cd backend && python -m pytest` |
| Delivery verifiers | **All 3 pass** | Commands in section 5 |

Measured synthetic results currently shown:

| Scenario | P50 shipped / target | P50 unmet | P50 freight | Recommendation at 90% P10 |
|---|---:|---:|---:|---|
| Normal | 1,577 / 1,577 | 0 | ₹4,027 | P80 |
| Scarce Supply | 969 / 1,577 | **608** | ₹2,344 | **None** (no level reaches 90%) |
| Expiry Trap | 1,577 / 1,577 | 0 | ₹4,609 | P80 |

Expiry Trap blocks **70** warehouse–batch options on shelf life (Normal: 7).
Scarce Supply's Risk Dial honestly reports that no level qualifies rather than
inventing a recommendation.

### Acceptance honesty

- Normal was **jointly reviewed** by both owners.
- Scarce Supply and Expiry Trap were completed while you were unavailable. They
  were independently rechecked by the app owner and recorded as **single-owner
  acceptance**, not joint sign-off. The exact wording and hashes are in
  `engine_results/index.json` and `docs/SCARCE_EXPIRY_REVIEW.md`.
- You do not need to rebuild them. A spot-check is enough if you want to sign off.

---

## 3. The one rule that must not break

**Never display or export a plan unless `checker.passed` is `true`.**

The app already enforces this. Keep it that way. The checker is a separate module
with no solver imports, and it rejects overselling, late arrival, short shelf
life, over-capacity, and shipments above target.

Also keep:

- `results/` (mock) separate from `engine_results/` (computed);
- canonical IDs `S01`–`S08`, `K01`–`K05`, `W01`–`W03`;
- synthetic framing: no real-world accuracy, savings, waste, or optimality claims;
- the app free of engine imports and the engine free of app imports.

---

## 4. Run the app

```bash
cd /home/eren/Travizthon/distrisense
source .venv/bin/activate
streamlit run app.py
```

Open http://localhost:8501. In the sidebar choose **Engine results**, then a
scenario. **Demo** mode is separate mock data.

---

## 5. Run the tests and verifiers

### Frontend (from the repo root)

```bash
cd /home/eren/Travizthon/distrisense
source .venv/bin/activate
python -m pytest
```

Expected: **67 passed**.

### Backend (separate environment)

Do not reuse the frontend environment. From the repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m pytest -q
```

Expected: **166 passed**.

Recheck every delivery:

```bash
python deliveries/normal-candidate/verify.py
python deliveries/normal-candidate/verify.py --rebuild
python deliveries/scarce-expiry-candidates/verify.py scarce_supply
python deliveries/scarce-expiry-candidates/verify.py expiry_trap
```

All four must pass. Recorded outputs are in each delivery's `verification/`
directory.

> **Why Normal has `frozen-code/`:** the Normal delivery was produced before
> `src/planner.py` was generalized for three scenarios. Its provenance pins the
> original code hash, so the delivery keeps a byte-for-byte copy of the code that
> produced it. The default verifier checks that copy; `--rebuild` proves the
> current planner reproduces all seven artifacts identically apart from solver
> timings. This is deliberate, not a workaround.

---

## 6. What remains

### P0 — finish before submission

1. **Manual visual QA (20–30 min).** In Engine results mode:
   - Normal: P50 ships 1,577, 0 unmet, CSV downloads.
   - Scarce Supply: 608 unmet visible; Risk Dial warns no level reaches 90%;
     LP beats greedy and pro-rata.
   - Expiry Trap: 70 shelf-life blocks; P50 has 0 unmet; P80 recommended.
   - Move the threshold slider to 100% in both stress scenarios and confirm the
     “no level reaches” warning.
   - No page errors; no mock/demo label while in Engine mode.
2. **Rehearse and record the demo.** Use `DEMO.md`; it has the exact numbers and
   the questions to expect. Record a backup video; do not rely on venue Wi-Fi.
3. **Submission polish.** Add screenshots if allowed; verify README and repo
   links; keep the app repo as the primary link.
4. **Confirm the old backend repo is frozen.** Optionally archive it on GitHub
   after submission.

### P1 — only if there is spare time

In value order:

1. Disruption toggle (warehouse or route outage) with re-optimization and
   comparison against the old plan.
2. FEFO preference with an expiry-risk comparison.
3. Bottleneck table for warehouses/routes at capacity.
4. Hindsight reference for the simulated draws.
5. CSV upload through the validator.

Do not start P1 before P0 is done and the demo is recorded.

---

## 7. Where to continue engine work

Work in `backend/`:

```bash
cd backend
source .venv/bin/activate
# edit src/, add tests, run python -m pytest -q
```

If you change engine output that should reach the UI:

1. Rebuild into a candidate directory — never overwrite `engine_results/` directly.
2. Re-run the independent verifier.
3. Copy only the seven UI JSON files into `engine_results/<scenario>/`.
4. Update `engine_results/index.json` with the new commits and acceptance scope.
5. Run the frontend suite before committing.

Scenario commands:

```bash
python -m src.engine normal
python -m src.planner --destination candidate_engine_results --scenario normal
python -m src.planner --destination candidate_engine_results --scenario scarce_supply
python -m src.planner --destination candidate_engine_results --scenario expiry_trap
```

Generated `data/`, `outputs/` and `candidate_engine_results/` are ignored; do not
commit them.

---

## 8. Cleanup — after submission only

The user asked to defer cleanup until the end. Do not delete anything yet. When
the submission is safely in:

- archive `rahullamani01/engine-module-` (do not delete);
- remove superseded handoffs: `HANDOFF.md`, `RAHUL_NEW_CHAT_HANDOFF.md`, and
  `docs/NEXT_DELIVERY_REQUEST.md` (it is already marked completed);
- decide whether to keep both `deliveries/` and `engine_results/` (the former is
  evidence, the latter is what the app reads);
- remove any regenerated local `data/`, `outputs/`, `candidate_engine_results/`,
  `__pycache__/` and `.pytest_cache/`.

---

## 9. Commit map

| Commit | What it is |
|---|---|
| `f61c73d` | Backend PR #1 merge — Normal accepted |
| `146d63d` | Normal delivery artifacts |
| `75b1a6c` | Normal accepted backend code head |
| `e94e05f` | Backend scenario planner generalization |
| `a514233` | Scarce/Expiry delivery package |
| `3eafc66` | Backend PR #2 merge — frozen snapshot source |
| `c30ec87` | Frontend activates all three scenarios |
| `adf2906` | Records backend merge commit |
| `759dab4` | Marks delivery request complete |
| `fae3933` | Demo export wording fix |
| `26db708` | Adds `backend/` snapshot + snapshot docs |

---

## 10. One-paragraph status

P0 is feature-complete and the demo is ready to rehearse. The remaining risk is
demo execution and visual QA, not missing engine work. All three scenarios are
computed, independently verified, and active; the old backend repo is frozen and
the engine is now in `backend/`. Tests are green on both sides (67 frontend, 166
backend). Finish the manual click-through, record a backup demo, submit, and only
then do cleanup or P1.
