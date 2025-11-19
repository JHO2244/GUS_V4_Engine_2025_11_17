# Centralized logging wrapper (stub)
"""
GUS v4 – Guardian Logging Stub (INFO = Green)

Provides a single helper:
    get_guardian_logger(name: str) -> logging.Logger

Behavior:
- INFO logs appear in green.
- WARNING logs appear in yellow.
- ERROR logs appear in red.
"""

from __future__ import annotations

import logging
import sys

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"

# Colorised level names
logging.addLevelName(logging.INFO, f"{COLOR_GREEN}INFO{COLOR_RESET}")
logging.addLevelName(logging.WARNING, f"{COLOR_YELLOW}WARN{COLOR_RESET}")
logging.addLevelName(logging.ERROR, f"{COLOR_RED}ERROR{COLOR_RESET}")


def get_guardian_logger(name: str) -> logging.Logger:
    """
    Return a preconfigured logger with colorised level names.

    - Only attaches a handler the first time a logger with this name is created.
    - Logs go to stdout so they appear in the Run/Terminal consoles.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(levelname)s %(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
