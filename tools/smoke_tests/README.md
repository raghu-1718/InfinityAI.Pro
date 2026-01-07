Smoke tests for InfinityAI.Pro

1. Prereqs

- Python 3.9+
- Install deps:

```bash
python -m pip install google-cloud-firestore google-cloud-secret-manager requests
```

- Authentication: set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON with Firestore and Secret Manager access, or use `gcloud auth application-default login`.

2. Scripts

- `check_collections.py` — inspects key Firestore collections used by the system.
- `compare_nifty.py` — fetches live NIFTY quote from Dhan and compares with Firestore `market_data/NIFTY`.

3. Run

```bash
python check_collections.py
python compare_nifty.py
```

Notes

- `compare_nifty.py` reads `DHAN_ACCESS_TOKEN` from env or from Secret Manager when `USE_SECRET_MANAGER=true`.
- These scripts are non-destructive and intended for smoke checks only.
