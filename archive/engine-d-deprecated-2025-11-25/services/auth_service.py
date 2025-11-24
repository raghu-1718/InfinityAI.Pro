# Archived from `engines/engine-d/services/auth_service.py` on 2025-11-25

```python
"""
Deprecated Engine D auth service.
This repo has migrated auth functionality to `engine-c-execution/services/auth_service.py`.
The file that previously contained demo users has been removed to avoid shipping credentials.
If you need to run auth locally, provide `JWT_SECRET_KEY` and `USERS_JSON` environment variables
or use the `auth_service` in Engine C.
"""
import logging

logger = logging.getLogger(__name__)

def _stub():
    raise RuntimeError("Engine D auth service removed. Use Engine C auth_service instead.")

```