# Minimal logging setup for Engine A
import logging
import sys
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "plain",
    log_file: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    logging.getLogger().handlers.clear()

    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handlers = []
    if enable_console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        handlers.append(ch)

    if log_file:
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            handlers.append(fh)
        except Exception:
            pass

    logging.basicConfig(level=level, handlers=handlers, force=True)
