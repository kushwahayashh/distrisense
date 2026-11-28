# v2 Phase 2 — M5 access and usage review

**Status:** Conditional / awaiting an authenticated download and terms review by the dataset recipient. No dataset was downloaded, no model was trained, and this document does not authorize using or republishing M5 data.

**Checked:** 28 November 2026. The accepted synthetic app and engine remain unchanged. This review is independent of the Phase 1 audit PR; the two PRs can be reviewed separately.

## Sources and verified facts

1. [University of Nicosia's M5 Competition overview](https://mofc.unic.ac.cy/m5-competition/) describes Walmart item-level *sales*, aggregated across product/store hierarchies in California, Texas and Wisconsin. It describes supplementary price, promotion, day-of-week and event information, and says many series are intermittent. This is background about data content, **not a usage license** or an inventory feed.
2. [Kaggle M5 Forecasting - Accuracy: data](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data) and [competition rules](https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules) are the intended primary source for the files and restrictions. The unauthenticated environment used for this review could **not retrieve or inspect these pages** (requests returned 404/no body). An unauthenticated API probe also did not yield a usable file inventory. Their contents and current download requirements are **unverified** here.
3. [Kaggle's CLI documentation](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) describes account authentication; [competition commands](https://github.com/Kaggle/kaggle-cli/blob/main/docs/competitions.md) document how to list/download competition files. This supports the local checks below, but does **not** imply that accepting a competition's rules grants commercial or redistribution rights.

## Local access checklist (Rahul; never commit credentials or raw files)

1. Open the linked **data** and **rules** pages while logged into your own Kaggle account. Record the exact dataset/competition URL, access or rule-acceptance requirement, any stated license and attribution, permitted research/commercial use, redistribution or public-output restrictions, and the date you viewed them. Save only your own notes or a short quote of relevant terms; do not paste credentials or personal account information.
2. To check access without downloading all data, use the documented CLI in a separate local environment:

   ```bash
   pipx install kaggle
   kaggle auth login
   kaggle competitions files m5-forecasting-accuracy
   ```

   If the command asks you to accept rules or authentication fails, resolve that on Kaggle first. **Do not paste tokens or `kaggle.json` into chat, issues, logs or Git.** Browser-based downloading is also fine.
3. Expect to look for daily item/store sales and a `d_####` day-to-date mapping (commonly called `sales_train_validation.csv` and `calendar.csv`). `sell_prices.csv` is useful later if pricing is in scope. These are **expected names to check**, not a claim that this session has confirmed the current file list. Record actual filenames, CSV headers, file sizes and whether the files open locally. Avoid sending the full CSVs; a sanitized header and column-count summary is enough for the next decision.
4. If available, keep downloaded files **outside the repository** in a private local directory; do not add them to Git or generate public samples until the terms are checked. If terms are unclear about public sample rows, publish **schema-only notes and synthetic fixtures**, not actual sales rows. Do not publish Kaggle access tokens.

## Mapping questions for Phase 3, not decided here

- Confirm the actual `item_id`, `store_id`, `d_####` and calendar `date` fields and whether the chosen five items have usable histories across eight stores. Eight distinct stores and the **same five products** yield 40 store–item pairs; do not silently pad absent combinations.
- The current engine fixes 40 pairs, 52 historical weeks, week 53 planning, and an anchored Monday calendar (`backend/src/config.py`, `backend/src/engine.py`, `backend/src/targets.py`). A valid 40-pair selection **still needs an agreed calendar/window mapping**; do not relabel old M5 dates as the accepted synthetic dates.
- Decide weekly aggregation rules (Monday–Sunday), partial-week handling, missing day versus recorded zero, how to represent intermittent sales, and a strictly chronological holdout before writing an adapter.
- M5 sales are **observed transactions**, not necessarily uncensored demand. M5 does not provide the current app's warehouse batch stock, route capacity/cost, expiry, or store opening stock. Any planner experiment using those inputs must label them **simulated** and remain separate from the accepted demo and real-sales backtest metrics.

## Phase 2 gate

**Not yet cleared.** Before proceeding to the 40-series selection and adapter:

- [ ] Logged-in user confirms the official file inventory and successful local access.
- [ ] Usage, attribution and redistribution/public-artifact restrictions are recorded from the actual provider terms, with URL and access date. Commercial usage remains **unverified** until specifically checked.
- [ ] Schema/header summary and file sizes are supplied without raw data or credentials.
- [ ] Both parties agree whether any actual sales rows may be published; default is **no**.

If Kaggle access or rights cannot be confirmed, evaluate another properly licensed dataset **before** coding around an unverified source.
