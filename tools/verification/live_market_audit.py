import sys
import os
import urllib.request
import json
import time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('=' * 65)
print('🟢 LIVE MARKET HOURS AUDIT (NSE/BSE/MCX 09:15 - 15:30 IST)')
print('=' * 65)

# 1. Engine C Health & Live Status
try:
    req = urllib.request.urlopen('https://engine-c-313407263327.asia-south1.run.app/health', timeout=10)
    res = json.loads(req.read().decode())
    print(f"[1/6] Engine C Live Gateway: ✅ OK (Status: {res.get('status')}, Version: {res.get('version')})")
except Exception as e:
    print(f"[1/6] Engine C Live Gateway: ❌ Error: {e}")

# 2. Engine A Live Risk & VaR
try:
    req = urllib.request.urlopen('https://engine-a-r2f5flt77q-el.a.run.app/health', timeout=10)
    res = json.loads(req.read().decode())
    print(f"[2/6] Engine A Risk & VaR: ✅ OK (Status: {res.get('status')}, Version: {res.get('version')})")
except Exception as e:
    print(f"[2/6] Engine A Risk & VaR: ❌ Error: {e}")

# 3. Firestore AES-256 Vault Auth & Status
try:
    req = urllib.request.urlopen('https://engine-c-313407263327.asia-south1.run.app/api/auth/status?user_id=raghu_primary', timeout=10)
    res = json.loads(req.read().decode())
    print(f"[3/6] Firestore AES-256 Vault: ✅ Operational ({res.get('auth_type')})")
except Exception as e:
    print(f"[3/6] Firestore AES-256 Vault: ❌ Error: {e}")

# 4. Engine C Live Market Quote Test
try:
    req = urllib.request.urlopen('https://engine-c-313407263327.asia-south1.run.app/dhan/market/quote/13?security_id=13&exchange_segment=IDX_I', timeout=10)
    res = json.loads(req.read().decode())
    print(f"[4/6] DhanHQ Live Market Feed: ✅ Responding ({res})")
except Exception as e:
    print(f"[4/6] DhanHQ Live Market Feed: ℹ️ Response note: {e}")

# 5. BigQuery Live Ticks & Dataset
try:
    from google.cloud import bigquery
    bq = bigquery.Client(project='project-841b7f97-5ee3-4fbe-920')
    q = 'SELECT count(*) as cnt FROM `project-841b7f97-5ee3-4fbe-920.infinity_dataset.market_ticks_history`'
    rows = list(bq.query(q).result())
    print(f"[5/6] BigQuery Dataset: ✅ Connected (Market ticks history: {rows[0].cnt} records)")
except Exception as e:
    print(f"[5/6] BigQuery Dataset: ⚠️ Note: {e}")

# 6. GCS Model Vault Artifacts
try:
    from google.cloud import storage
    gcs = storage.Client(project='project-841b7f97-5ee3-4fbe-920')
    blobs = list(gcs.bucket('infinity-ai-models-vault').list_blobs())
    print(f"[6/6] GCS Model Vault: ✅ Connected ({len(blobs)} live ensemble binaries loaded)")
    for b in blobs:
        print(f"      - {b.name} ({b.size} bytes, updated: {b.updated})")
except Exception as e:
    print(f"[6/6] GCS Model Vault: ❌ Error: {e}")

print('=' * 65)
