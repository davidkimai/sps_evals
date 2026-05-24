from __future__ import annotations


def reconcile_entries(entries: list[dict]) -> dict:
    totals = {}
    for entry in entries:
        direction = entry.get('direction')
        if direction not in {'debit', 'credit'}:
            raise ValueError('unknown direction')
        account = entry['account']
        amount = entry.get('amount', 0)
        bucket = totals.setdefault(account, {'debit': 0, 'credit': 0, 'balance': 0})
        bucket[direction] += amount
        bucket['balance'] = bucket['credit'] - bucket['debit']
    return totals
