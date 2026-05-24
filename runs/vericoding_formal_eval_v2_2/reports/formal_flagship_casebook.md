# Formal Flagship Casebook

## timing_safe_compare / timing_safe_compare:gpt-5.4-mini:alt_seed_or_temp_prompt:formal:5
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  import hmac from typing import Union   def _validate_operand(value: object, name: str) -> Union[str, bytes]: if isinstance(value, (str, bytes)): return value raise TypeError(f"{name} must be str or bytes")

## timing_safe_compare / timing_safe_compare:gpt-5.4-mini:requirements_first_prompt:formal:2
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  import hmac from typing import Union   def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool: """ Compare two values in a timing-safe manner. 

## timing_safe_compare / timing_safe_compare:gpt-5.4-mini:self_critique_prompt:formal:4
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  import hmac from typing import Union   def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool: if type(left) is not type(right): raise TypeError("left and right must have the same type") if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)):

## timing_safe_compare / timing_safe_compare:gpt-5.4-mini:structural_discipline_prompt:formal:3
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  import hmac from typing import Union   def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool: if not isinstance(left, (str, bytes)): raise TypeError("left must be str or bytes") if not isinstance(right, (str, bytes)):

## timing_safe_compare / timing_safe_compare:gpt-5.5:alt_seed_or_temp_prompt:formal:11
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: import hmac from typing import Union  Comparable = Union[str, bytes]  __all__ = ["timing_safe_compare"]   def _require_supported_pair(left: object, right: object) -> None: left_type = type(left)

## timing_safe_compare / timing_safe_compare:gpt-5.5:requirements_first_prompt:formal:8
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: import hmac from typing import Union  Comparable = Union[str, bytes]   def timing_safe_compare(left: Comparable, right: Comparable) -> bool: """Compare two strings or byte strings using hmac.compare_digest.""" if type(left) not in (str, bytes): raise TypeError("left must be str or bytes")

## timing_safe_compare / timing_safe_compare:gpt-5.5:self_critique_prompt:formal:10
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: import hmac from typing import Union  ComparableValue = Union[str, bytes]   def timing_safe_compare(left: ComparableValue, right: ComparableValue) -> bool: """ Compare two str or bytes values using hmac.compare_digest. 

## timing_safe_compare / timing_safe_compare:gpt-5.5:structural_discipline_prompt:formal:9
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: """Timing-safe comparison helper."""  from __future__ import annotations  import hmac   def timing_safe_compare(left: str | bytes, right: str | bytes) -> bool: """Compare two str or bytes values using hmac.compare_digest. 

