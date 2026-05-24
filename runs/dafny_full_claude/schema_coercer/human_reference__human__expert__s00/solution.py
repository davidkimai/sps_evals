from __future__ import annotations


def coerce_schema(raw: dict, schema: dict) -> dict:
    output = {}
    for field, (caster, default) in schema.items():
        value = raw.get(field, default)
        try:
            output[field] = caster(value)
        except Exception as exc:
            raise ValueError(f'could not coerce {field}') from exc
    return output
