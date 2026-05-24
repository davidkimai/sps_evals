import csv
from io import StringIO


def aggregate_sales(csv_text: str) -> list[dict]:
    totals: dict[tuple[str, str], dict[str, int]] = {}
    for row in csv.DictReader(StringIO(csv_text)):
        parsed = _parse_row(row)
        if parsed is None:
            continue
        region, product, quantity, cents = parsed
        bucket = totals.setdefault((region, product), {"quantity": 0, "cents": 0})
        bucket["quantity"] += quantity
        bucket["cents"] += cents
    return [
        {
            "region": region,
            "product": product,
            "quantity": values["quantity"],
            "cents": values["cents"],
        }
        for (region, product), values in sorted(totals.items())
    ]


def _parse_row(row: dict) -> tuple[str, str, int, int] | None:
    region = (row.get("region") or "").strip()
    product = (row.get("product") or "").strip()
    if not region or not product:
        return None
    try:
        return region, product, int(row.get("quantity", "")), int(row.get("cents", ""))
    except ValueError:
        return None
