# v2 Phase 1 — accepted-demo baseline audit

**Audit date:** 27 November 2026
**Repository:** `kushwahayashh/distrisense`
**Audited base:** `639d992feb2d8c3e7ecec8e5a72a776d3de332c9` (`main`)
**Scope:** Read-only inspection and verification of the existing synthetic prototype. This document does not approve M5 usage or change the accepted demo.

## Ownership and boundaries

- `backend/` is the canonical engine copy. `backend/SNAPSHOT.md` identifies its origin as the frozen standalone backend at `3eafc66`. Do not push engine changes to the old repository.
- The Streamlit app consumes saved `engine_results/` artifacts and never runs the engine on clicks. `results/` contains mock demo artifacts and must remain separate.
- `engine_results/index.json` currently activates `normal`, `scarce_supply`, and `expiry_trap`; Normal has joint acceptance, while the two stress scenarios have recorded single-owner acceptance. No acceptance flags or artifacts were edited in this audit.
- `RAHUL_HANDOFF.md` supersedes the earlier handoffs. The accepted demo and its synthetic-only claims remain the baseline for v2.

## Independent checks run on a clean app checkout

The app and engine were tested in **separate** Python environments on macOS / Python 3.14.4.

| Check | Result | Command / interpretation |
|---|---|---|
| App suite | **67 passed in 2.51 s** | `.venv-phase1/bin/python -m pytest -v` at repo root, with app requirements installed in an isolated, ignored venv. |
| Backend suite | **166 passed in 45.77 s** | Backend-pinned environment: `python -m pytest -q` from `backend/`. |
| Normal verifier | **PASS** | `python deliveries/normal-candidate/verify.py` from `backend/`. |
| Normal rebuild verifier | **PASS** | Same command with `--rebuild`; seven outputs identical apart from timings. |
| Scarce verifier | **PASS** | `python deliveries/scarce-expiry-candidates/verify.py scarce_supply`. |
| Expiry verifier | **PASS** | Same command with `expiry_trap`. |
| Saved-artifact inspection | **PASS** | Active index; seven JSON objects per scenario (rejecting non-finite JSON); each has 40 unique forecast pairs, six ordered checked LP levels and a 200-draw Risk Dial. This inspection is not a substitute for the independent verifiers. |

Backend verifier evidence: 18 independently checked method/level plans per scenario, common 200 × 40 demand draws, continuous LP bounds, reproduced evaluation and recommendation, and input/code hashes. The Normal verifier checks the producing frozen-code snapshot; `--rebuild` checks current-planner equivalence.

**Environment caveat:** An initial app test attempt using a pre-existing environment without Streamlit failed during collection (`ModuleNotFoundError`). After installing the app requirements into a separate environment, all 67 tests passed. That failed attempt is not a product failure. The app environment resolved Streamlit 1.49.1, pandas 2.3.3, NumPy 2.5.5, scikit-learn 1.9.1 and SciPy 1.18.1; the backend run used NumPy 2.4.4, pandas 3.0.2, scikit-learn 1.8.0 and SciPy 1.17.1. Do not treat cross-version retraining as bitwise reproducible; preserve the accepted forecast.

## Accepted-artifact fingerprints and sample outcomes

SHA-256 fingerprints (from the audited base):

| Path | SHA-256 |
|---|---|
| `engine_results/index.json` | `eceba1b479f313658b00b1c57dffe3778933c09d159efd6e8e8ad69fa6b68dcc` |
| Each of `engine_results/{normal,scarce_supply,expiry_trap}/forecast.json` | `f969efd5091e8629c46dee7da73eb276655594ebdf58ab1a632981984c679f1c` |
| `data/normal/opening_stock.csv` | `2045636c9672687d22d3e31ec3689a2cdf15cb87e6d46d6ce448773cf06f992c` |

| Scenario | P50 target / shipped / unmet | P50 freight | Shelf-life blocks | Default 90% P10 recommendation |
|---|---|---:|---:|---|
| Normal | 1,577 / 1,577 / 0 | ₹4,027 | 7 | P80 |
| Scarce Supply | 1,577 / 969 / 608 | ₹2,344 | 7 | None |
| Expiry Trap | 1,577 / 1,577 / 0 | ₹4,609 | 70 | P80 |

These are **synthetic-data results**, not evidence of real-world forecast accuracy, savings, reduced waste or integer optimality. This phase does **not** perform manual visual QA, obtain retailer data, check M5 access/licensing, run real-sales backtests, or verify production readiness.

## v2 design constraints found (not implementation decisions)

- `backend/src/schemas.py` expects `demand_history.csv` with `week_start,store_id,sku_id,units_sold`; its internal `to_weekly` view is `store_id,sku_id,week,demand`. Week 1 is anchored to the earliest date and successive weeks are a seven-day grid.
- `backend/src/config.py` fixes eight stores, five SKUs, 40 pairs, Monday anchor `2025-01-06`, 52 history weeks, planning week 53, fit weeks 5–40, holdout weeks 41–52 and refit weeks 5–52. `backend/src/engine.py` and `backend/src/targets.py` explicitly check 40 rows and planning week 53. Selecting an M5 subset with 40 pairs alone does **not** remove the fixed calendar/window assumptions.
- Target computation is `max(0, ceil(quantile) - opening_units)`; the planner's real operational inputs are not present in M5 and cannot be called real without a separate authorized source.
- Future sales, synthetic planning-week hidden truth and test-set outcomes must not enter feature fitting or allocation decisions. Real sales may understate demand when stockouts occur.

## Exit status and next gate

**Phase 1 complete as a reproducible code/artifact baseline, not as visual QA or market readiness.** Phase 2 should verify M5 download access, permitted usage/redistribution, required files and available columns **before** committing any source data. Phase 3 must agree on M5 store/item → canonical-ID mapping, week boundaries, missing-day/week policy, chronological split and source labels before writing an adapter. Leave the accepted synthetic mode unchanged while those decisions are open.
