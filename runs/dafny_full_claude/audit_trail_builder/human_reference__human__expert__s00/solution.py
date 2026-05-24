from __future__ import annotations


def build_audit_trail(events: list[dict]) -> list[dict]:
    records = []
    for index, event in enumerate(events, start=1):
        if not event.get('source_system') or not event.get('actor_id'):
            raise ValueError('source_system and actor_id are required')
        records.append({'sequence': index, 'source_system': event['source_system'], 'actor_id': event['actor_id'], 'action': event.get('action')})
    return records
