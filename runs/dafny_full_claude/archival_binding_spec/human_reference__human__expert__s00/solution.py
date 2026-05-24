def parse_bindings(lines: list[str]) -> dict[str, dict[str, str]]:
    binding_ledger: dict[str, dict[str, str]] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        cleaned_line = raw_line.strip()
        if not cleaned_line or cleaned_line.startswith("#"):
            continue
        section, key, value = _split_binding_line(cleaned_line, line_number)
        section_ledger = binding_ledger.setdefault(section, {})
        section_ledger[key] = value
    return binding_ledger


def _split_binding_line(line: str, line_number: int) -> tuple[str, str, str]:
    if "=" not in line or "." not in line.split("=", 1)[0]:
        raise ValueError(f"line {line_number} is malformed")
    left, value = line.split("=", 1)
    section, key = [part.strip() for part in left.split(".", 1)]
    if not section:
        raise ValueError(f"section is empty on line {line_number}")
    if not key:
        raise ValueError(f"key is empty on line {line_number}")
    return section, key, value.strip()
