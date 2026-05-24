def parse_cli_args(argv: list[str]) -> dict:
    parsed = {"input": None, "limit": 100, "format": "json", "dry_run": False}
    index = 0
    while index < len(argv):
        flag = argv[index]
        if flag == "--dry-run":
            parsed["dry_run"] = True
            index += 1
        elif flag in {"--input", "--limit", "--format"}:
            value = _require_value(argv, index, flag)
            if flag == "--input":
                parsed["input"] = value
            elif flag == "--limit":
                parsed["limit"] = _positive_int(value, flag)
            else:
                if value not in {"json", "csv"}:
                    raise ValueError("--format must be json or csv")
                parsed["format"] = value
            index += 2
        else:
            raise ValueError(f"unknown flag: {flag}")
    if parsed["input"] is None:
        raise ValueError("--input is required")
    return parsed


def _require_value(argv: list[str], index: int, flag: str) -> str:
    if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
        raise ValueError(f"{flag} requires a value")
    return argv[index + 1]


def _positive_int(value: str, flag: str) -> int:
    if not value.isdigit() or int(value) <= 0:
        raise ValueError(f"{flag} must be a positive integer")
    return int(value)
