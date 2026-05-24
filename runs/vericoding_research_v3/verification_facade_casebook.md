# Verification Facade Casebook

This casebook is intentionally bounded to 5-10 worked examples. It records concrete review-boundary risks rather than a giant taxonomy.

## policy_merge

- accept: Accept implementations that satisfy visible behavior and hidden day-2 regression checks without widening the component boundary.
- reject: Reject visible-passing candidates that fail hidden edge cases, state transitions, precedence rules, or tenant/security boundaries.
- must review: Review the natural-language spec, executable oracle assumptions, wrapper/runtime boundary, dependency behavior, and whether accepted outputs are safe to ship in the intended deployment context.
- facade risk: visible tests or proof-shaped artifacts may certify behavior that differs from deployed wrapper/runtime behavior.

## config_precedence_merge

- accept: Accept implementations that satisfy visible behavior and hidden day-2 regression checks without widening the component boundary.
- reject: Reject visible-passing candidates that fail hidden edge cases, state transitions, precedence rules, or tenant/security boundaries.
- must review: Review the natural-language spec, executable oracle assumptions, wrapper/runtime boundary, dependency behavior, and whether accepted outputs are safe to ship in the intended deployment context.
- facade risk: visible tests or proof-shaped artifacts may certify behavior that differs from deployed wrapper/runtime behavior.

## cli_argument_validation

- accept: Accept implementations that satisfy visible behavior and hidden day-2 regression checks without widening the component boundary.
- reject: Reject visible-passing candidates that fail hidden edge cases, state transitions, precedence rules, or tenant/security boundaries.
- must review: Review the natural-language spec, executable oracle assumptions, wrapper/runtime boundary, dependency behavior, and whether accepted outputs are safe to ship in the intended deployment context.
- facade risk: visible tests or proof-shaped artifacts may certify behavior that differs from deployed wrapper/runtime behavior.

## parser_validator_edges

- accept: Accept only implementations that pass visible behavior and hidden adversarial security checks for the stated boundary.
- reject: Reject visible-passing candidates that bypass canonicalization, authorization, isolation, or redaction constraints.
- must review: Review the natural-language spec, executable oracle assumptions, wrapper/runtime boundary, dependency behavior, and whether accepted outputs are safe to ship in the intended deployment context.
- facade risk: visible tests or proof-shaped artifacts may certify behavior that differs from deployed wrapper/runtime behavior.

## input_canonicalization

- accept: Accept only implementations that pass visible behavior and hidden adversarial security checks for the stated boundary.
- reject: Reject visible-passing candidates that bypass canonicalization, authorization, isolation, or redaction constraints.
- must review: Review the natural-language spec, executable oracle assumptions, wrapper/runtime boundary, dependency behavior, and whether accepted outputs are safe to ship in the intended deployment context.
- facade risk: visible tests or proof-shaped artifacts may certify behavior that differs from deployed wrapper/runtime behavior.

## authorization_rule_sequence

- accept: Accept only implementations that pass visible behavior and hidden adversarial security checks for the stated boundary.
- reject: Reject visible-passing candidates that bypass canonicalization, authorization, isolation, or redaction constraints.
- must review: Review the natural-language spec, executable oracle assumptions, wrapper/runtime boundary, dependency behavior, and whether accepted outputs are safe to ship in the intended deployment context.
- facade risk: visible tests or proof-shaped artifacts may certify behavior that differs from deployed wrapper/runtime behavior.
