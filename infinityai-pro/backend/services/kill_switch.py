"""
Simple persistent kill-switch service for InfinityAI.Pro

Stores a small JSON file under the backend directory that tracks:
- enabled: bool  (True = trading allowed)
- consecutive_failures: int

Provides helpers to check and mutate the state.
"""
import json
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_STATE_FILE = Path(__file__).resolve().parents[1] / "kill_switch.json"


def _read_state():
    if not _STATE_FILE.exists():
        return {"enabled": False, "consecutive_failures": 0, "last_alert": None}
    try:
        with _STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read kill-switch state: {e}")
        return {"enabled": False, "consecutive_failures": 0, "last_alert": None}


def _write_state(state: dict):
    try:
        with _STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception as e:
        logger.error(f"Failed to write kill-switch state: {e}")


def is_enabled() -> bool:
    return bool(_read_state().get("enabled", False))


def set_enabled(value: bool):
    state = _read_state()
    state["enabled"] = bool(value)
    if value:
        state["consecutive_failures"] = 0
    _write_state(state)
    logger.info(f"Kill-switch set to {'ENABLED' if value else 'DISABLED'}")


def get_consecutive_failures() -> int:
    return int(_read_state().get("consecutive_failures", 0))


def reset_failures():
    state = _read_state()
    state["consecutive_failures"] = 0
    _write_state(state)
    logger.info("Kill-switch failures reset to 0")


def record_failure(emergency_contact: str | None = None) -> int:
    state = _read_state()
    count = int(state.get("consecutive_failures", 0)) + 1
    state["consecutive_failures"] = count

    # If threshold reached, disable trading and record alert timestamp
    if count >= 2:
        state["enabled"] = False
        state["last_alert"] = {
            "at": datetime.utcnow().isoformat() + "Z",
            "reason": f"{count} consecutive order failures",
            "contact": emergency_contact,
        }
        logger.warning(f"Kill-switch triggered after {count} consecutive failures. Emergency contact: {emergency_contact}")
        # Append to local alert log for operators
        try:
            alert_log = Path(__file__).resolve().parents[1] / "kill_switch_alerts.log"
            with alert_log.open("a", encoding="utf-8") as lf:
                lf.write(json.dumps(state["last_alert"]) + "\n")
        except Exception as e:
            logger.error(f"Failed to write kill-switch alert log: {e}")

    _write_state(state)
    return count
