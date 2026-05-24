"""Registry for packaged Agent Skills used by modular discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / "data" / "skills"


@dataclass(frozen=True)
class SkillRecord:
    skill_id: str
    name: str
    description: str
    path: Path
    content: str


SKILL_PATHS: dict[str, Path] = {
    "zen": _SKILLS_ROOT / "zen-of-python-oracle" / "SKILL.md",
    "karpathy": _SKILLS_ROOT / "karpathy-guidelines-oracle" / "SKILL.md",
    "dafny": _SKILLS_ROOT / "dafny-formal-verification" / "SKILL.md",
}


def get_skill(skill_id: str) -> SkillRecord:
    """Load a packaged SKILL.md by short registry id."""
    if skill_id not in SKILL_PATHS:
        valid = ", ".join(sorted(SKILL_PATHS))
        raise KeyError(f"unknown skill_id {skill_id!r}; expected one of: {valid}")
    path = SKILL_PATHS[skill_id]
    frontmatter, body = _split_skill_file(path)
    return SkillRecord(
        skill_id=skill_id,
        name=str(frontmatter["name"]),
        description=str(frontmatter["description"]),
        path=path,
        content=body.strip(),
    )


def available_skills() -> tuple[SkillRecord, ...]:
    return tuple(get_skill(skill_id) for skill_id in sorted(SKILL_PATHS))


def render_skill_catalog() -> str:
    lines = []
    for skill in available_skills():
        lines.append(f"- {skill.skill_id}: {skill.name} - {skill.description}")
    return "\n".join(lines)


def get_skill_tool_schema() -> dict[str, Any]:
    """Return an Anthropic-style strict tool schema for loading packaged skills."""
    return {
        "name": "get_skill",
        "description": "Load the full markdown content for one packaged SpecOracle skill.",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill_id": {
                    "type": "string",
                    "enum": sorted(SKILL_PATHS),
                    "description": "Short id of the skill to load.",
                }
            },
            "required": ["skill_id"],
            "additionalProperties": False,
        },
    }


def _split_skill_file(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        raise FileNotFoundError(path)
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"SKILL.md at {path} lacks YAML frontmatter")
    try:
        _, frontmatter_text, body = content.split("---\n", 2)
    except ValueError as exc:
        raise ValueError(f"SKILL.md at {path} lacks closing frontmatter delimiter") from exc
    frontmatter = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(frontmatter, dict):
        raise ValueError(f"SKILL.md at {path} frontmatter must be a mapping")
    for key in ("name", "description"):
        if not frontmatter.get(key):
            raise ValueError(f"SKILL.md at {path} lacks required frontmatter field: {key}")
    if not body.strip():
        raise ValueError(f"SKILL.md at {path} has empty body")
    return frontmatter, body
