from __future__ import annotations


REGRESSION_STRESSORS: tuple[str, ...] = (
    "dropped_branch",
    "regression_revert",
    "silently_incomplete_implementation",
    "visible_pass_hidden_fail",
    "structurally_neat_semantically_wrong",
)


def is_regression_sensitive(surface: str, tags: list[str] | tuple[str, ...] = ()) -> bool:
    tag_text = " ".join(tags).lower()
    return surface == "scbench_regression" or any(
        marker in tag_text
        for marker in ("state", "policy", "permission", "config", "schema", "regression")
    )
