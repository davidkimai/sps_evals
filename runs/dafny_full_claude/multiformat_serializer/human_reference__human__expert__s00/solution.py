from __future__ import annotations

import json


def serialize_record(record: dict, format: str) -> str:
    if format == 'json':
        return json.dumps(record, sort_keys=True)
    if format == 'csv':
        keys = list(record)
        return ','.join(keys) + '\n' + ','.join(str(record[key]) for key in keys)
    if format == 'toml':
        lines = []
        for key, value in record.items():
            rendered = json.dumps(value) if isinstance(value, str) else str(value)
            lines.append(f'{key} = {rendered}')
        return '\n'.join(lines)
    raise ValueError('unsupported format')
