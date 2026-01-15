"""
GUS v4 CORE FREEZE ANCHOR

This module declares the immutable boundary of GUS v4.
No runtime behavior. No configuration. No overrides.

Only v5+ may change semantics.
"""

GUS_V4_CORE_FROZEN = True

V4_CORE_INCLUDES = {
    "gdvs",
    "sealing_and_verification",
    "integrity_invariants",
    "policy_spine",
    "deterministic_evaluation_logic",
    "refusal_semantics",
}

V4_CORE_EXCLUDES = {
    "ui",
    "apis",
    "adapters",
    "presentation_logic",
    "business_rules",
    "market_specific_behavior",
    "runtime_configuration",
    "overrides",
}

SEMANTIC_CHANGE_FORBIDDEN_IN_V4 = True
