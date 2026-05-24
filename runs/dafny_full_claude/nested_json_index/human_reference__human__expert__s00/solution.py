from __future__ import annotations


def build_user_purchase_index(events: list[dict]) -> dict[str, dict[str, int]]:
    index: dict[str, dict[str, int]] = {}
    for event in events:
        user_id = event.get("user_id")
        amount = event.get("amount")
        if event.get("kind") != "purchase":
            continue
        if not isinstance(user_id, str) or not user_id:
            continue
        if not isinstance(amount, int):
            continue

        totals = index.setdefault(user_id, {"count": 0, "total": 0})
        totals["count"] += 1
        totals["total"] += amount
    return index
