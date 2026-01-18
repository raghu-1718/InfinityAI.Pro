"""
Cloud Resource Audit & Cleanup Script
Analyzes all GCP resources and identifies duplicates/unused resources
"""
import subprocess
import json
from datetime import datetime

PROJECT_ID = "galvanic-pulsar-482815-h0"
REGION = "us-central1"

print("=" * 80)
print("  INFINITYAI.PRO - CLOUD RESOURCE AUDIT")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Get all Cloud Run services
result = subprocess.run([
    'gcloud', 'run', 'services', 'list',
    '--region', REGION,
    '--project', PROJECT_ID,
    '--format', 'json'
], capture_output=True, text=True)

services = json.loads(result.stdout)

print(f"\n[1] CLOUD RUN SERVICES ({len(services)} total)")
print("-" * 60)

# Categorize services
CORE_ENGINES = ['engine-a', 'engine-b', 'engine-c']
CLOUD_FUNCTIONS = [
    'analyzeportfolio', 'backtest-orchestrator', 'detect-momentum-signals',
    'fetchaccountdata', 'get-latest-signals', 'get-live-prices',
    'get-price-history', 'getaisignals', 'getbatchaisignals',
    'getdhanoverview', 'getgeminianalysis', 'getvertexaianalysis',
    'live-data-ingestion', 'starttrading', 'stoptrading',
    'storeusercredentials', 'verifycoupon'
]

core = []
functions = []
unknown = []

for svc in services:
    name = svc['metadata']['name']
    url = svc['status'].get('url', 'N/A')
    
    if name in CORE_ENGINES:
        core.append({'name': name, 'url': url, 'status': 'ESSENTIAL'})
    elif name in CLOUD_FUNCTIONS:
        functions.append({'name': name, 'url': url, 'status': 'CLOUD FUNCTION'})
    else:
        unknown.append({'name': name, 'url': url, 'status': 'REVIEW'})

print("\n  CORE ENGINES (ESSENTIAL - DO NOT DELETE):")
for svc in core:
    print(f"    ✅ {svc['name']}: {svc['url'][:50]}...")

print(f"\n  CLOUD FUNCTIONS ({len(functions)} services):")
for svc in functions:
    print(f"    📦 {svc['name']}")

if unknown:
    print(f"\n  ⚠️ UNKNOWN/REVIEW ({len(unknown)} services):")
    for svc in unknown:
        print(f"    ❓ {svc['name']}")

# Secrets analysis
print("\n" + "-" * 60)
print("[2] SECRETS MANAGER")
print("-" * 60)

result = subprocess.run([
    'gcloud', 'secrets', 'list',
    '--project', PROJECT_ID,
    '--format', 'json'
], capture_output=True, text=True)

secrets = json.loads(result.stdout)

ESSENTIAL_SECRETS = ['dhan-access-token', 'dhan-api-secret', 'dhan-client-id', 'encryption-key', 'gemini-api-key']
TEST_SECRETS = ['dhan_creds_test']
OTHER = ['openai-api-key']

for secret in secrets:
    name = secret['name'].split('/')[-1]
    if name in ESSENTIAL_SECRETS:
        print(f"    ✅ {name} (ESSENTIAL)")
    elif name in TEST_SECRETS:
        print(f"    ⚠️ {name} (TEST - CAN DELETE)")
    else:
        print(f"    📦 {name}")

# Artifact Registry
print("\n" + "-" * 60)
print("[3] ARTIFACT REGISTRY")
print("-" * 60)

result = subprocess.run([
    'gcloud', 'artifacts', 'repositories', 'list',
    '--location', REGION,
    '--project', PROJECT_ID,
    '--format', 'json'
], capture_output=True, text=True)

repos = json.loads(result.stdout)
for repo in repos:
    name = repo['name'].split('/')[-1]
    print(f"    📦 {name} ({repo['format']})")

# Storage Buckets
print("\n" + "-" * 60)
print("[4] STORAGE BUCKETS")
print("-" * 60)

result = subprocess.run([
    'gcloud', 'storage', 'buckets', 'list',
    '--project', PROJECT_ID,
    '--format', 'json'
], capture_output=True, text=True)

try:
    buckets = json.loads(result.stdout)
    for bucket in buckets:
        name = bucket['name']
        if 'cloudbuild' in name:
            print(f"    🔧 {name} (BUILD ARTIFACTS)")
        elif 'appspot' in name:
            print(f"    🔥 {name} (FIREBASE)")
        else:
            print(f"    📦 {name}")
except:
    print("    Unable to list buckets")

# Summary
print("\n" + "=" * 80)
print("  CLEANUP RECOMMENDATIONS")
print("=" * 80)

print("""
  SAFE TO DELETE:
    - dhan_creds_test (test secret)
    - Old/unused Cloud Run revisions (auto-cleanup recommended)

  KEEP (ESSENTIAL):
    - engine-a, engine-b, engine-c (Core engines)
    - All Cloud Functions (Firebase Gen2)
    - dhan-access-token, dhan-api-secret, dhan-client-id
    - encryption-key, gemini-api-key
    - infinityai artifact repository

  REVIEW:
    - openai-api-key (if not using OpenAI, can delete)
    - cloud-run-source-deploy repository (auto-generated)
    - gcf-artifacts repository (Cloud Functions)
""")

print("=" * 80)
