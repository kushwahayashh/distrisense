# v2 Phase 2 — M5 access and usage review

**Status:** Local files inspected. The user supplied the M5 Accuracy competition rules text (headed "Updated March 24, 2020"); it limits dataset use to non-commercial purposes and restricts redistribution. M5 is a conditional choice for non-commercial research, **not cleared as a commercial training-data source**. No data was copied into the repository or used to train a model.

**Checked:** 28 November 2026. The accepted synthetic app and engine remain unchanged. This review is independent of the Phase 1 audit PR; the two PRs can be reviewed separately.

## Sources and verified facts

1. [University of Nicosia's M5 Competition overview](https://mofc.unic.ac.cy/m5-competition/) describes Walmart item-level *sales*, aggregated across product/store hierarchies in California, Texas and Wisconsin. It describes supplementary price, promotion, day-of-week and event information, and says many series are intermittent. This is background about data content, **not a usage license** or an inventory feed.
2. [Kaggle M5 Forecasting - Accuracy: data](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data) and [competition rules](https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules) are the intended primary source for the files and restrictions. The unauthenticated environment used for this review could **not retrieve or inspect these pages** (requests returned 404/no body). An unauthenticated API probe also did not yield a usable file inventory. Their contents and current download requirements are **unverified** here.
3. [Kaggle's CLI documentation](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) describes account authentication; [competition commands](https://github.com/Kaggle/kaggle-cli/blob/main/docs/competitions.md) document how to list/download competition files. This supports the local checks below, but does **not** imply that accepting a competition's rules grants commercial or redistribution rights.

### Rules supplied by the user (confirm against your logged-in page)

The text the user pasted from the [M5 Accuracy competition rules](https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules) states:

- Competition-specific **"DATA ACCESS AND USE: Competition Use, Academic, Non-Commercial Use"**. General rule B.7.A permits use of competition data **"for non-commercial purposes only"**, including competition participation, academic research and education.
- Rule B.7.B requires reasonable safeguards against access by people who have not agreed to the rules, and prohibits transmitting, publishing, redistributing or otherwise providing competition data to nonparticipants. Do not put raw or row-level data in a public repository, app, example, PR or downloadable artifact. Treat public derived examples conservatively until the provider clarifies their status.
- Rule A.1's **open-source winner license** is about a winner's *submission/code*, **not** a commercial license for Walmart's competition data. A product cannot treat that paragraph as a data license.

These are readings of user-provided rules text, not legal advice; the Kaggle page itself was not retrievable from the unauthenticated review environment. Confirm the current full rules and your own acceptance/access status on Kaggle. **No commercial training, deployment or redistribution based on this dataset** without independently secured rights. For a market-ready product, obtain properly licensed commercial data or a retailer agreement. Keep any M5 experiment local/non-commercial and its outputs clearly separate from the accepted synthetic demo.

## Local file inspection (no data published)

Rahul supplied a local `m5-forecasting-accuracy/` folder **outside Git**. Filenames, byte sizes and CSV headers were read locally; this verifies file presence and parseable headers, **not** provenance, provider checksums or license rights.

| File | Bytes | Header / shape |
|---|---:|---|
| `calendar.csv` | 103,469 | 14 columns: `date,wm_yr_wk,weekday,wday,month,year,d,event_name_1,event_type_1,event_name_2,event_type_2,snap_CA,snap_TX,snap_WI`; 1,969 rows, `d_1` (`2011-01-29`, Saturday) through `d_1969` (`2016-06-19`, Sunday). |
| `sales_train_validation.csv` | 120,007,726 | 30,490 rows, six ID columns `id,item_id,dept_id,cat_id,store_id,state_id`, then `d_1` through `d_1913` (1,919 total columns). |
| `sales_train_evaluation.csv` | 121,736,518 | 30,490 rows, the same six ID columns, then `d_1` through `d_1941` (1,947 total columns). |
| `sell_prices.csv` | 203,395,785 | `store_id,item_id,wm_yr_wk,sell_price` (four columns); full row count not inspected. |
| `sample_submission.csv` | 5,228,786 | `id,F1` through `F28` (29 columns); full row count not inspected. |

A streaming pass over the first six columns of **both** sales files found 10 store IDs (`CA_1`–`CA_4`, `TX_1`–`TX_3`, `WI_1`–`WI_3`), 3,049 distinct items and 30,490 distinct store–item pairs in each file. This does **not** establish that every pair has nonzero or sufficiently complete weekly history. The validation file ends at `d_1913` and evaluation file at `d_1941`; the calendar continues to `d_1969`. Decide explicitly which available daily range is eligible for training/holdout and never use future sales during fitting.

## Local access checklist (Rahul; never commit credentials or raw files)

1. Open the linked **data** and **rules** pages while logged into your own Kaggle account. Confirm the supplied March 2020 rules are current, record the source URL, rule-acceptance requirement and date viewed, and check whether the files came from this exact competition. Save only notes or a short quote; do not paste credentials or personal account information. **A local file copy alone does not establish rights.**
2. To confirm the competition file list or source using the documented CLI in a separate local environment, if needed:

   ```bash
   pipx install kaggle
   kaggle auth login
   kaggle competitions files m5-forecasting-accuracy
   ```

   If the command asks you to accept rules or authentication fails, resolve that on Kaggle first. **Do not paste tokens or `kaggle.json` into chat, issues, logs or Git.** Browser-based downloading is also fine.
3. Keep downloaded files **outside the repository** in a private local directory; do not add them to Git or generate public samples until the terms are checked. If terms are unclear about public sample rows, publish **schema-only notes and synthetic fixtures**, not actual sales rows. Do not publish Kaggle access tokens.

## Mapping questions for Phase 3, not decided here

- Confirm the actual `item_id`, `store_id`, `d_####` and calendar `date` fields and whether the chosen five items have usable histories across eight stores. Eight distinct stores and the **same five products** yield 40 store–item pairs; do not silently pad absent combinations.
- The current engine fixes 40 pairs, 52 historical weeks, week 53 planning, and an anchored Monday calendar (`backend/src/config.py`, `backend/src/engine.py`, `backend/src/targets.py`). A valid 40-pair selection **still needs an agreed calendar/window mapping**; do not relabel old M5 dates as the accepted synthetic dates.
- Decide weekly aggregation rules (Monday–Sunday), partial-week handling, missing day versus recorded zero, how to represent intermittent sales, and a strictly chronological holdout before writing an adapter.
- M5 sales are **observed transactions**, not necessarily uncensored demand. M5 does not provide the current app's warehouse batch stock, route capacity/cost, expiry, or store opening stock. Any planner experiment using those inputs must label them **simulated** and remain separate from the accepted demo and real-sales backtest metrics.

## Phase 2 gate

**Research-only conditional; commercial use is not cleared.** Before proceeding to a local, non-commercial 40-series feasibility experiment:

- [x] Local files open; schema, headers, sizes and sales-pair counts recorded without publishing rows.
- [x] User supplied competition rules text explicitly restricting dataset use to non-commercial purposes and restricting redistribution. This is **not** a commercial-use authorization.
- [ ] Logged-in user confirms these files came from the official competition and matches the authenticated file inventory.
- [ ] Logged-in user confirms the supplied rules text against the current source, their acceptance status and any additional public-output/attribution restrictions. Do not assume commercial rights.
- [ ] Both parties agree whether any actual sales rows may be published; default is **no**.

For commercial training or deployment, select another dataset with explicit commercial rights or obtain written permission from the relevant rightsholder(s); M5's competition rules as supplied do **not** grant that right. If local research access cannot be confirmed, choose another properly licensed source before writing an adapter.
