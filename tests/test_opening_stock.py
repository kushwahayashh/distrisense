import csv

import pytest

from scripts.make_opening_stock import ROOT, build_opening_stock, validate_opening_stock


def test_seeded_stock_matches_delivered_csv():
    rows = build_opening_stock()
    assert rows == build_opening_stock()
    validate_opening_stock(rows)
    with (ROOT / "data/normal/opening_stock.csv").open(newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["store_id", "sku_id", "opening_units"]
        saved = [dict(row, opening_units=int(row["opening_units"])) for row in reader]
    assert saved == rows
    assert all(0 <= row["opening_units"] <= 20 for row in rows)


@pytest.mark.parametrize("quantity", [-1, 1.5, True, "20"])
def test_rejects_invalid_quantities(quantity):
    rows = build_opening_stock()
    rows[0]["opening_units"] = quantity
    with pytest.raises(ValueError):
        validate_opening_stock(rows)


def test_rejects_missing_duplicate_and_unknown_pairs():
    rows = build_opening_stock()
    for invalid in (rows[:-1], [rows[0], *rows[:-1]], [dict(rows[0], store_id="S99"), *rows[1:]]):
        with pytest.raises(ValueError):
            validate_opening_stock(invalid)
