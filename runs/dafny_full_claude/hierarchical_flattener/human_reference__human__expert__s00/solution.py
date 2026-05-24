from __future__ import annotations


def flatten_paths(value: dict) -> dict[str, object]:
    output = {}

    def visit(prefix: str, item) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                visit(f'{prefix}.{key}' if prefix else str(key), child)
        else:
            output[prefix] = item

    visit('', value)
    return output
