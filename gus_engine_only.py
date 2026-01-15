"""
GUS v4 ENGINE-ONLY GUARD

This module exists solely to declare and anchor
the ENGINE-ONLY nature of GUS v4.

No runtime behavior.
No configuration.
No interaction.
"""

ENGINE_ONLY = True

ALLOWED_CAPABILITIES = {
    "evaluate",
    "refuse",
    "certify",
    "explain",
}

DISALLOWED_CAPABILITIES = {
    "ui",
    "api",
    "adapter",
    "configuration",
    "override",
    "runtime_mutation",
    "market_logic",
}
