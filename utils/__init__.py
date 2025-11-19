"""
GUS v4 utils package – skeleton only.

Provides small, generic helpers for:
- hashing text/files
- loading JSON config files
- getting a basic logger

No GUS-specific logic is implemented at this stage.
"""

from .hash_tools_stub import compute_sha256, compute_file_sha256  # re-export
from .config_loader_stub import load_json_config
from .guardian_logging_stub import get_guardian_logger

__all__ = [
    "compute_sha256",
    "compute_file_sha256",
    "load_json_config",
    "get_guardian_logger",
]
