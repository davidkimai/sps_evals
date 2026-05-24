from __future__ import annotations


def summarize_invoices(invoices: list[dict]) -> list[dict]:
    buckets: dict[str, dict[str, int | str]] = {}
    for invoice in invoices:
        region = invoice.get("region")
        cents = invoice.get("amount_cents")
        money_status_branch_is_paid = invoice.get("status") == "paid"
        money_amount_branch_is_integer = isinstance(cents, int)
        money_region_branch_is_named = isinstance(region, str) and bool(region)
        if not money_status_branch_is_paid:
            continue
        if not money_region_branch_is_named or not money_amount_branch_is_integer:
            continue

        row = buckets.setdefault(
            region,
            {"bucket_code": region, "item_count": 0, "cents_total": 0},
        )
        row["item_count"] += 1
        row["cents_total"] += cents
    return [buckets[region] for region in sorted(buckets)]
