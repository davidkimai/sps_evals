from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecureTaskTemplate:
    task_id: str
    category: str
    summary: str
    failure_label: str


SECURE_TASKS: tuple[SecureTaskTemplate, ...] = (
    SecureTaskTemplate(
        "safe_path_validation",
        "path_validation",
        "Normalize user paths and reject traversal outside an allowed root.",
        "path_traversal_acceptance",
    ),
    SecureTaskTemplate(
        "shell_argument_construction",
        "shell_args",
        "Build subprocess argument vectors without shell-string injection.",
        "shell_injection_acceptance",
    ),
    SecureTaskTemplate(
        "archive_extract_filter",
        "archive",
        "Filter archive members before extraction to prevent zip-slip writes.",
        "archive_traversal_acceptance",
    ),
    SecureTaskTemplate(
        "url_domain_allowlist",
        "url_validation",
        "Validate canonical hostnames against an allowlist.",
        "domain_confusion_acceptance",
    ),
    SecureTaskTemplate(
        "parser_validator_edges",
        "parser",
        "Reject malformed records while preserving valid edge cases.",
        "parser_misclassification",
    ),
    SecureTaskTemplate(
        "input_canonicalization",
        "canonicalization",
        "Canonicalize equivalent identifiers before applying policy.",
        "canonicalization_bypass",
    ),
    SecureTaskTemplate(
        "authorization_rule_sequence",
        "authorization",
        "Apply deny rules before allow rules and record the matched rule.",
        "authorization_order_bypass",
    ),
    SecureTaskTemplate(
        "config_schema_enforcement",
        "schema",
        "Enforce config schema defaults without silently accepting unknown keys.",
        "schema_unknown_key_acceptance",
    ),
    SecureTaskTemplate(
        "token_scope_checker",
        "authorization",
        "Check token scope and expiry before accepting privileged actions.",
        "scope_or_expiry_bypass",
    ),
    SecureTaskTemplate(
        "redaction_policy_engine",
        "privacy",
        "Redact protected fields before serializing user-facing logs.",
        "sensitive_field_exposure",
    ),
    SecureTaskTemplate(
        "webhook_signature_validator",
        "integrity",
        "Validate webhook signatures with canonical payload bytes.",
        "signature_validation_bypass",
    ),
    SecureTaskTemplate(
        "rate_limit_key_builder",
        "abuse_prevention",
        "Build stable tenant-scoped rate-limit keys.",
        "tenant_boundary_bypass",
    ),
)


def hidden_oracle_hash(task_id: str) -> str:
    import hashlib

    digest = hashlib.sha256(f"vericoding-hidden-oracle:{task_id}:v1".encode("utf-8"))
    return digest.hexdigest()
