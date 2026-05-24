"""Load oracle specifications from Agent Skills SKILL.md files."""

from __future__ import annotations

import re
from pathlib import Path


def load_skill_oracle(path: str | Path) -> tuple[str, str]:
    """Parse a SKILL.md file and return the skill name plus oracle body."""
    skill_path = Path(path)
    content = skill_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        raise ValueError(
            f"SKILL.md at {skill_path} lacks valid YAML frontmatter (--- delimiters)"
        )

    frontmatter, body = match.groups()
    name = _frontmatter_value(frontmatter, "name")
    description = _frontmatter_value(frontmatter, "description")
    if not name:
        raise ValueError(f"SKILL.md at {skill_path} lacks a 'name' field in frontmatter")
    if not description:
        raise ValueError(
            f"SKILL.md at {skill_path} lacks a 'description' field in frontmatter"
        )

    oracle_body = body.strip()
    if not oracle_body:
        raise ValueError(f"SKILL.md at {skill_path} has empty body (no oracle text)")
    return name, oracle_body


def _frontmatter_value(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", frontmatter, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if value in {">-", "|"}:
        return value
    return value.strip("\"'")
