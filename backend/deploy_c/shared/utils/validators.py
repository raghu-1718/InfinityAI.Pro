import logging
import sys
from typing import Optional

logger = logging.getLogger("shared.validators")


def is_placeholder_value(value: Optional[str]) -> bool:
    """Return True if the given value looks like a placeholder or test token."""
    if value is None:
        return True
    v = str(value).strip()
    if v == "":
        return True
    up = v.upper()
    # Common sentinel strings we treat as invalid placeholders
    for sentinel in ("PLACEHOLDER", "TEST_TOKEN", "DUMMY", "NO_VALUE"):
        if sentinel in up:
            return True
    return False


def assert_no_placeholder(name: str, value: Optional[str]):
    """Fail-fast if a critical configuration value is missing or clearly a placeholder.

    This intentionally exits the process to make misconfiguration obvious in production.
    Callers should guard so this only runs for admin/global credentials (not per-user tokens).
    """
    if is_placeholder_value(value):
        logger.fatal(f"[FATAL] {name} is missing or contains a placeholder value: {value!r}")
        # Ensure the message appears in logs and then exit with non-zero
        sys.exit(1)
    return True
