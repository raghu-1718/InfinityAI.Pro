# Thin wrapper to maintain the requested v4.5 structure
# Delegates to existing implementation in backend/engines/engine-a/main.py

import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engines.engine-a.main import app  # type: ignore  # FastAPI app

# Uvicorn will import app from here: `uvicorn backend.engine-a.main:app`
