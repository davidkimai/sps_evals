# Formal Flagship Casebook

## feature_flag_matrix / feature_flag_matrix:gpt-5.4-mini:alt_seed_or_temp_prompt:formal:6
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  from typing import Any   def _copy_defaults(defaults: dict[str, bool]) -> dict[str, bool]: return dict(defaults)   def _apply_segment_overrides(

## feature_flag_matrix / feature_flag_matrix:gpt-5.4-mini:baseline_prompt:formal:0
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  from typing import Dict, List, Any   def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]: """ Resolve feature flags from defaults, segment overrides, and user overrides.  Rules:

## feature_flag_matrix / feature_flag_matrix:gpt-5.4-mini:invariants_first_prompt:formal:3
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  from typing import Dict, List, Any   def resolve_flags( defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict, ) -> dict[str, bool]:

## feature_flag_matrix / feature_flag_matrix:gpt-5.4-mini:requirements_first_prompt:formal:2
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  from typing import Dict, Any   def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]: """ Resolve feature flags from defaults, segment overrides, and user overrides.  Rules:

## feature_flag_matrix / feature_flag_matrix:gpt-5.4-mini:self_critique_prompt:formal:5
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  from copy import deepcopy from typing import Any   def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]: """ Resolve feature flags from defaults, segment overrides, and user overrides. 

## feature_flag_matrix / feature_flag_matrix:gpt-5.4-mini:structural_discipline_prompt:formal:4
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from __future__ import annotations  from typing import Any   def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]: result: dict[str, bool] = dict(defaults)  user_segments = user.get("segments") if isinstance(user_segments, list):

## feature_flag_matrix / feature_flag_matrix:gpt-5.4-mini:visible_harness_only_prompt:formal:1
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from typing import Dict, Any   def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]: result: dict[str, bool] = dict(defaults)  user_segments = user.get("segments", []) if isinstance(user_segments, list): for segment_name in user_segments: if segment_name in segments:

## feature_flag_matrix / feature_flag_matrix:gpt-5.5:alt_seed_or_temp_prompt:formal:14
- visible_tests_pass: True
- formal_pass: False
- harness_status: visible_pass_formal_fail
- code_summary: from typing import Any   def _copy_mapping_values(source: dict[str, bool]) -> dict[str, bool]: return dict(source)   def _segment_names_for_user(user: dict[str, Any]) -> list[str]: names = user.get("segments", []) if names is None:

