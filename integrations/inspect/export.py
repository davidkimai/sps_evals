#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Export SpecOracle results for Inspect integration.")
    parser.add_argument("run_dir", help="SpecOracle run directory containing summary.csv")
    parser.add_argument("--out", default="integrations/inspect/inspect_results.json")
    args = parser.parse_args()

    payload = export_run(Path(args.run_dir))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.resolve())
    return 0


def export_run(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)
    with summary_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("variant") or "unknown")].append(row)

    return {
        "schema": "specoracle.inspect_export.v1",
        "run_dir": str(run_dir),
        "summary_csv": str(summary_path),
        "row_count": len(rows),
        "variants": {
            variant: {
                "rows": len(group),
                "models": sorted(
                    {
                        f"{row.get('provider', '')}/{row.get('model', '')}"
                        for row in group
                        if row.get("provider") and row.get("model")
                    }
                ),
                "pytest_pass_rate": _pass_rate(group, "pytest_passed"),
                "stress_pass_rate": _pass_rate(group, "stress_passed"),
                "cc_average": _mean_float(group, "cc_average"),
                "judge_score": _mean_float(group, "judge_score"),
            }
            for variant, group in sorted(groups.items())
        },
    }


def _pass_rate(rows: list[dict[str, str]], field: str) -> float | None:
    values = [row.get(field) for row in rows if row.get(field) not in {None, ""}]
    if not values:
        return None
    passed = sum(1 for value in values if str(value).lower() == "true")
    return round(passed / len(values) * 100.0, 1)


def _mean_float(rows: list[dict[str, str]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) not in {None, ""}]
    return round(mean(values), 3) if values else None


if __name__ == "__main__":
    raise SystemExit(main())
