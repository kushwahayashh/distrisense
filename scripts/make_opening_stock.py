"""Generate synthetic normal-scenario opening stock, not shipment allocations."""

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORES = [f"S{i:02d}" for i in range(1, 9)]
SKUS = [f"K{i:02d}" for i in range(1, 6)]


def build_opening_stock(seed=42):
    # Assumption: 0–20 units on hand per pair. No forecasts/hidden truth used.
    rng = random.Random(seed)
    return [
        {"store_id": store, "sku_id": sku, "opening_units": rng.randint(0, 20)}
        for store in STORES for sku in SKUS
    ]


def validate_opening_stock(rows):
    expected = {(store, sku) for store in STORES for sku in SKUS}
    pairs = [(row["store_id"], row["sku_id"]) for row in rows]
    if len(pairs) != 40 or len(set(pairs)) != 40 or set(pairs) != expected:
        raise ValueError("Expected exactly the 40 unique S01–S08 / K01–K05 pairs.")
    for row in rows:
        units = row["opening_units"]
        if isinstance(units, bool) or not isinstance(units, int) or units < 0:
            raise ValueError("Opening stock must contain nonnegative integer units.")


def main():
    rows = build_opening_stock()
    validate_opening_stock(rows)
    output = ROOT / "data" / "normal" / "opening_stock.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing inventory: {output}")
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["store_id", "sku_id", "opening_units"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {output}: {len(rows)} validated synthetic stock records (seed 42).")


if __name__ == "__main__":
    main()
