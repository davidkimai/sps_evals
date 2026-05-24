# Formal Review Boundary Casebook

## timing_safe_compare / timing_safe_compare:gpt-5.4-mini:behavioral_minimal_prompt:formal:0
- formal_pass: True
- review_reason: The bounded formal I/O cases do not certify constant-time behavior. Human review should confirm use of compare_digest or an equivalent primitive before automatic authorization.
- code_summary: from typing import Optional   def timing_safe_compare(left, right, pad_to_length: int | None = None, pad_char: str = "\0") -> bool: if type(left) is not type(right): raise TypeError("left and right must have the same type")  if isinstance(left, bytes): if pad_to_length is not None: raise TypeError("padding is supported only for strings")

## timing_safe_compare / timing_safe_compare:gpt-5.5:behavioral_minimal_prompt:formal:6
- formal_pass: True
- review_reason: The bounded formal I/O cases do not certify constant-time behavior. Human review should confirm use of compare_digest or an equivalent primitive before automatic authorization.
- code_summary: def timing_safe_compare(left, right, pad_to_length: int | None = None, pad_char: str = "\0") -> bool: if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)): raise TypeError("left and right must be str or bytes")  if type(left) is not type(right): raise TypeError("left and right must have the same type")  if pad_to_length is None: return left == right 

