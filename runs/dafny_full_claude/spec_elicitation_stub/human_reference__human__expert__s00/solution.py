from __future__ import annotations


def handle_underspecified(payload: dict):
    if payload.get('mode') == 'echo' and 'value' in payload:
        return payload['value']
    raise NotImplementedError('uncovered input path')
