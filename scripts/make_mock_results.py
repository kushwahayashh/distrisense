#!/usr/bin/env python3
"""Generate deterministic mock engine artifacts for UI development.

This is NOT the engine. It produces plausible files that match CONTRACT.md so
the Streamlit app can be built, demoed and reviewed before the real pipeline
exists. Every number is synthetic and must never be presented as a result.

Run:  python scripts/make_mock_results.py
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"

LEVELS = [
    ("P50", 1.00),
    ("P60", 1.07),
    ("P70", 1.14),
    ("P80", 1.21),
    ("P90", 1.30),
    ("P95", 1.40),
]
LEVEL_NAMES = [name for name, _ in LEVELS]

WAREHOUSES = ["W1", "W2", "W3"]
STORES = [f"S{i}" for i in range(1, 9)]
SKUS = [f"SKU{i:02d}" for i in range(1, 6)]

LOST_SALE = 12
OVERSTOCK = 3
LATEST_ARRIVAL = 2
MIN_SHELF = 3
PLANNING_MONDAY = date(2026, 10, 26)

SCENARIOS = {
    "normal": {
        "name": "Normal",
        "stock_mult": 1.25,
        "inactive_rate": 0.06,
        "expiry_trap": False,
        "base_fulfill": 0.880,
        "fulfill_step": 0.018,
        "pinball": {"baseline_ma4": 3.84, "ml_gbm": 3.91},
    },
    "scarce": {
        "name": "Scarce Supply",
        "stock_mult": 0.55,
        "inactive_rate": 0.14,
        "expiry_trap": False,
        "base_fulfill": 0.660,
        "fulfill_step": 0.025,
        "pinball": {"baseline_ma4": 4.21, "ml_gbm": 4.08},
    },
    "expiry": {
        "name": "Expiry Trap",
        "stock_mult": 1.15,
        "inactive_rate": 0.06,
        "expiry_trap": True,
        "base_fulfill": 0.720,
        "fulfill_step": 0.022,
        "pinball": {"baseline_ma4": 3.62, "ml_gbm": 3.55},
    },
}


def r2(value: float) -> float:
    return round(float(value), 3)


def build_scenario(key: str, cfg: dict, idx: int) -> dict:
    rng = random.Random(SEED + idx * 100)

    # ---- routes -----------------------------------------------------------
    routes = {}
    for w in WAREHOUSES:
        for s in STORES:
            active = rng.random() > cfg["inactive_rate"]
            routes[(w, s)] = {
                "unit_cost": rng.randint(1, 6),
                "lead_time": rng.randint(0, 3),
                "active": active,
                "capacity_units": 600,
            }

    # Guarantee at least one blocked option per rule, as the PRD requires.
    routes[("W3", STORES[-1])]["active"] = False
    routes[("W2", STORES[-2])]["lead_time"] = 3

    # ---- batches ----------------------------------------------------------
    batches = []
    for w in WAREHOUSES:
        for sku in SKUS:
            for b in range(2):
                units = max(10, int(rng.randint(120, 220) * cfg["stock_mult"]))
                if cfg["expiry_trap"] and w == "W1":
                    expiry_offset = rng.randint(3, 5)  # cheap stock that expires
                    unit_hint = 1
                else:
                    expiry_offset = rng.randint(8, 40)
                    unit_hint = None
                batches.append(
                    {
                        "batch_id": f"{w}-{sku}-B{b + 1}",
                        "warehouse_id": w,
                        "sku_id": sku,
                        "units": units,
                        "expiry_offset": expiry_offset,
                        "cheap": unit_hint,
                    }
                )

    # Guarantee at least one shelf-life-blocked option in every scenario.
    for b in batches:
        if b["warehouse_id"] == "W3" and b["sku_id"] == "SKU05" and b["batch_id"].endswith("B2"):
            b["expiry_offset"] = 3

    # Expiry Trap: make W1 the cheapest warehouse so the trap is tempting.
    if cfg["expiry_trap"]:
        for (w, s), route in routes.items():
            if w == "W1":
                route["unit_cost"] = 1

    # ---- store stock and demand ------------------------------------------
    store_factor = {s: rng.uniform(0.80, 1.25) for s in STORES}
    demand = {}
    store_stock = {}
    for s in STORES:
        for sku in SKUS:
            demand[(s, sku)] = int(rng.randint(40, 150) * store_factor[s])
            store_stock[(s, sku)] = rng.randint(0, 40)

    # ---- eligibility / blocked counts ------------------------------------
    blocked = {"route": 0, "lead_time": 0, "shelf_life": 0}
    for b in batches:
        for s in STORES:
            route = routes[(b["warehouse_id"], s)]
            arrival = route["lead_time"]
            if not route["active"]:
                blocked["route"] += 1
            elif arrival > LATEST_ARRIVAL:
                blocked["lead_time"] += 1
            elif b["expiry_offset"] - arrival < MIN_SHELF:
                blocked["shelf_life"] += 1

    # ---- plans ------------------------------------------------------------
    def build_level(mult: float) -> dict:
        remaining = {b["batch_id"]: b["units"] for b in batches}
        used = defaultdict(int)
        shipments = []
        unmet = []
        total_target = total_shipped = 0

        for s in STORES:
            for sku in SKUS:
                target = max(0, round(demand[(s, sku)] * mult) - store_stock[(s, sku)])
                total_target += target
                need = target

                options = []
                for b in batches:
                    if b["sku_id"] != sku:
                        continue
                    route = routes[(b["warehouse_id"], s)]
                    if not route["active"]:
                        continue
                    if route["lead_time"] > LATEST_ARRIVAL:
                        continue
                    shelf = b["expiry_offset"] - route["lead_time"]
                    if shelf < MIN_SHELF:
                        continue
                    options.append((route["unit_cost"], route["lead_time"], b, shelf))
                options.sort(key=lambda o: (o[0], o[1]))

                for cost, lead, b, shelf in options:
                    if need <= 0:
                        break
                    cap_left = routes[(b["warehouse_id"], s)]["capacity_units"] - used[(b["warehouse_id"], s)]
                    take = min(need, remaining[b["batch_id"]], cap_left)
                    if take <= 0:
                        continue
                    remaining[b["batch_id"]] -= take
                    used[(b["warehouse_id"], s)] += take
                    need -= take
                    shipments.append(
                        {
                            "warehouse_id": b["warehouse_id"],
                            "store_id": s,
                            "sku_id": sku,
                            "batch_id": b["batch_id"],
                            "units": int(take),
                            "unit_cost": int(cost),
                            "freight": int(take * cost),
                            "arrival_day": int(lead),
                            "shelf_life_on_arrival": int(shelf),
                            "expiry_date": (PLANNING_MONDAY + timedelta(days=b["expiry_offset"])).isoformat(),
                        }
                    )

                shipped = target - need
                total_shipped += shipped
                if need > 0:
                    unmet.append(
                        {
                            "store_id": s,
                            "sku_id": sku,
                            "target_units": int(target),
                            "shipped_units": int(shipped),
                            "unmet_units": int(need),
                        }
                    )

        shipments.sort(key=lambda x: (x["warehouse_id"], x["store_id"], x["sku_id"]))
        freight = sum(x["freight"] for x in shipments)
        return {
            "shipments": shipments,
            "unmet": unmet,
            "blocked": dict(blocked),
            "totals": {
                "target_units": int(total_target),
                "shipped_units": int(total_shipped),
                "unmet_units": int(total_target - total_shipped),
                "freight": int(freight),
                "shipments": len(shipments),
            },
            "checker": {"passed": True, "violations": []},
        }

    plans = {name: build_level(mult) for name, mult in LEVELS}

    # ---- risk dial --------------------------------------------------------
    # Realized service improves as the planning level rises: more cover is
    # bought with more freight. Cost is U-shaped (shortage falls, overstock
    # rises). This is a synthetic illustration, not a measured result.
    total_demand = sum(demand.values())
    dial = []
    for i, (name, _) in enumerate(LEVELS):
        totals = plans[name]["totals"]
        fulfill = min(0.985, cfg["base_fulfill"] + i * cfg["fulfill_step"])
        p10 = fulfill - 0.050
        expected_short = total_demand * (1 - fulfill)
        excess = totals["shipped_units"] * (0.04 + 0.02 * i)
        realized = totals["freight"] + LOST_SALE * expected_short + OVERSTOCK * excess
        dial.append(
            {
                "level": name,
                "freight": totals["freight"],
                "realized_cost_mean": r2(realized),
                "realized_cost_p90": r2(realized * 1.14),
                "fulfillment_mean": r2(fulfill),
                "fulfillment_p10": r2(p10),
                "shipped_units": totals["shipped_units"],
                "unmet_units": int(round(expected_short)),
            }
        )

    # ---- baselines (compared at P50) -------------------------------------
    p50 = plans["P50"]["totals"]
    d50 = dial[0]
    lp_planned = p50["freight"] + LOST_SALE * p50["unmet_units"]
    baseline_rows = [
        {
            "id": "lp",
            "name": "LP optimizer",
            "planned_objective": int(lp_planned),
            "realized_cost_mean": d50["realized_cost_mean"],
            "fulfillment_mean": d50["fulfillment_mean"],
            "fulfillment_p10": d50["fulfillment_p10"],
            "freight": d50["freight"],
            "unmet_units": d50["unmet_units"],
            "checker_passed": True,
        },
        {
            "id": "pro_rata",
            "name": "Pro-rata",
            "planned_objective": int(lp_planned * 1.07),
            "realized_cost_mean": r2(d50["realized_cost_mean"] * 1.05),
            "fulfillment_mean": r2(d50["fulfillment_mean"] - 0.015),
            "fulfillment_p10": r2(d50["fulfillment_p10"] - 0.018),
            "freight": int(d50["freight"] * 1.03),
            "unmet_units": int(d50["unmet_units"] * 1.08),
            "checker_passed": True,
        },
        {
            "id": "greedy",
            "name": "Cheapest-first greedy",
            "planned_objective": int(lp_planned * 1.14),
            "realized_cost_mean": r2(d50["realized_cost_mean"] * 1.09),
            "fulfillment_mean": r2(d50["fulfillment_mean"] - 0.030),
            "fulfillment_p10": r2(d50["fulfillment_p10"] - 0.035),
            "freight": int(d50["freight"] * 1.08),
            "unmet_units": int(d50["unmet_units"] * 1.16),
            "checker_passed": True,
        },
    ]

    # ---- evaluation -------------------------------------------------------
    scores = cfg["pinball"]
    selected = "baseline_ma4" if scores["baseline_ma4"] <= scores["ml_gbm"] else "ml_gbm"
    offsets = [-0.02, 0.01, 0.03, 0.02, -0.01, 0.02]
    calibration = []
    for i, name in enumerate(LEVEL_NAMES):
        nominal = float(name[1:]) / 100
        observed = round(nominal + offsets[i], 3)
        calibration.append(
            {
                "level": name,
                "nominal": nominal,
                "observed": observed,
                "within_tolerance": abs(observed - nominal) <= 0.10,
            }
        )

    # ---- forecast table ---------------------------------------------------
    forecast_rows = []
    for s in STORES:
        for sku in SKUS:
            row = {
                "store_id": s,
                "sku_id": sku,
                "opening_units": store_stock[(s, sku)],
            }
            for name, mult in LEVELS:
                row[name.lower()] = int(round(demand[(s, sku)] * mult))
            row["target_p50"] = max(0, row["p50"] - row["opening_units"])
            row["target_p90"] = max(0, row["p90"] - row["opening_units"])
            forecast_rows.append(row)

    # ---- validation -------------------------------------------------------
    files = [
        ("products.csv", len(SKUS)),
        ("locations.csv", len(WAREHOUSES) + len(STORES)),
        ("inventory_batches.csv", len(batches)),
        ("store_inventory.csv", len(STORES) * len(SKUS)),
        ("routes.csv", len(WAREHOUSES) * len(STORES)),
        ("demand_history.csv", len(STORES) * len(SKUS) * 52),
        ("config.json", 1),
    ]
    validation = {
        "ok": True,
        "files": [
            {"name": name, "rows": rows, "status": "ok", "errors": 0, "warnings": 0}
            for name, rows in files
        ],
        "checks": [
            {"id": "schema", "label": "Required columns present", "passed": True, "detail": "7 files"},
            {"id": "no_negative", "label": "No negative quantities or costs", "passed": True, "detail": ""},
            {"id": "unique_ids", "label": "IDs are unique", "passed": True, "detail": ""},
            {"id": "references", "label": "No orphan references", "passed": True, "detail": ""},
            {"id": "dates", "label": "Dates parse and expiry is in the future", "passed": True, "detail": ""},
            {"id": "levels", "label": "Forecast quantiles never cross", "passed": True, "detail": ""},
            {"id": "leakage", "label": "Forecast uses past weeks only", "passed": True, "detail": ""},
        ],
        "errors": [],
        "warnings": [
            {
                "file": "demand_history.csv",
                "row": 173,
                "column": "units_sold",
                "rule": "short_series",
                "message": "Fewer than 20 residuals for S6/SKU04; SKU-pooled residuals used.",
            },
            {
                "file": "inventory_batches.csv",
                "row": 22,
                "column": "expiry_date",
                "rule": "expiring_soon",
                "message": "W1-SKU03-B2 expires within 7 days of the planning week.",
            },
            {
                "file": "routes.csv",
                "row": 19,
                "column": "is_active",
                "rule": "inactive_route",
                "message": "Route W3->S8 is inactive and was excluded from eligibility.",
            },
        ],
    }

    meta = {
        "scenario_id": key,
        "scenario_name": cfg["name"],
        "planning_week": "2026-W44",
        "seed": SEED,
        "forecaster_used": selected,
        "forecaster_scores": scores,
        "solver_status": "optimal",
        "solve_time_seconds": round(0.18 + idx * 0.07, 2),
        "levels": LEVEL_NAMES,
        "default_level": "P50",
        "network": {"warehouses": len(WAREHOUSES), "stores": len(STORES), "skus": len(SKUS)},
        "latest_arrival_day": LATEST_ARRIVAL,
        "min_shelf_life_days": MIN_SHELF,
    }

    return {
        "meta": meta,
        "validation": validation,
        "forecast": {"rows": forecast_rows},
        "plan": {"scenario_id": key, "levels": plans},
        "risk_dial": {"draws": 200, "levels": dial},
        "baselines": {"levels": ["P50"], "methods": baseline_rows},
        "evaluation": {
            "pinball": {
                "scored_weeks": "41-52",
                "baseline_ma4": scores["baseline_ma4"],
                "ml_gbm": scores["ml_gbm"],
                "selected": selected,
            },
            "calibration": calibration,
            "expiry_risk_units": 41 + idx * 12,
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"generated_at": "2026-10-24T18:00:00", "mock": True, "scenarios": []}

    for idx, (key, cfg) in enumerate(SCENARIOS.items()):
        payload = build_scenario(key, cfg, idx)
        folder = OUT / key
        folder.mkdir(parents=True, exist_ok=True)
        for name, data in payload.items():
            (folder / f"{name}.json").write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        index["scenarios"].append(
            {"id": key, "name": cfg["name"], "path": f"results/{key}"}
        )
        print(f"wrote {folder.relative_to(ROOT)} ({len(payload)} files)")

    (OUT / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"wrote {(OUT / 'index.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
