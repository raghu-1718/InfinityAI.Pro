# v4.5 structure entrypoint delegating to backend/engines/engine-d/main.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engines.engine-d.main import app  # type: ignore
