import json
import os
import glob
from datetime import datetime

CENSUS_DIR = "artifacts/cloud_census"
REPORT_FILE = "artifacts/CLOUD_CENSUS_REPORT.md"

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read {path}: {e}")
        return []

def generate_markdown():
    lines = []
    lines.append("# Cloud Forensic Census Report")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Compute
    lines.append("## 1. Compute & Serverless")
    
    # Cloud Run
    services = load_json(f"{CENSUS_DIR}/compute/cloud_run.json")
    if services:
        lines.append("\n### Cloud Run Services")
        lines.append("| Service | Region | Image | Type |")
        lines.append("|---|---|---|---|")
        for s in services:
            name = s['metadata']['name']
            region = s['metadata']['labels'].get('cloud.googleapis.com/location', 'unknown')
            image = s['spec']['template']['spec']['containers'][0]['image']
            
            # Classification
            rtype = "UNKOWN"
            if name in ['engine-a', 'engine-b', 'engine-c']:
                rtype = "✅ CORE"
            elif 'syncholdings' in name or 'trading' in name:
                rtype = "⚠️ LEGACY?"
            else:
                rtype = "❓ OTHER"

            lines.append(f"| `{name}` | {region} | `{os.path.basename(image)}` | {rtype} |")
    else:
        lines.append("\n- No Cloud Run Services found.")

    # Functions
    funcs = load_json(f"{CENSUS_DIR}/compute/functions.json")
    if funcs:
        lines.append("\n### Cloud Functions")
        lines.append("| Name | Runtime | Status | Trigger |")
        lines.append("|---|---|---|---|")
        for f in funcs:
            trigger = "HTTP" if 'httpsTrigger' in f else "Event"
            lines.append(f"| `{f['name'].split('/')[-1]}` | {f.get('runtime', 'N/A')} | {f.get('status', 'UNKNOWN')} | {trigger} |")
    else:
        lines.append("\n- No Cloud Functions found.")

    # 2. Data
    lines.append("\n## 2. Data & Storage")
    buckets = load_json(f"{CENSUS_DIR}/data/storage_buckets.json")
    if buckets:
        lines.append("\n### Storage Buckets")
        lines.append("| Name | Class | Classification |")
        lines.append("|---|---|---|")
        for b in buckets:
            name = b.get('name', 'N/A')
            cls = b.get('default_storage_class', b.get('storageClass', 'UNKNOWN'))
            
            # Classification
            if name.startswith('gcf-'):
                status = "🤖 Auto (Functions)"
            elif name.startswith('run-sources'):
                status = "🤖 Auto (Cloud Run)"
            elif 'cloudbuild' in name:
                status = "🤖 Auto (Build)"
            elif 'terraform' in name:
                status = "🛠️ Infra"
            elif 'trading-history' in name or 'ml-models' in name:
                status = "✅ CORE DATA"
            else:
                status = "❓ UNKNOWN"

            lines.append(f"| `{name}` | {cls} | {status} |")

    # 3. AI
    lines.append("\n## 3. Vertex AI")
    models = load_json(f"{CENSUS_DIR}/ai/vertex_models.json")
    if models:
        lines.append("\n### Models")
        for m in models:
            lines.append(f"- **{m.get('displayName', 'N/A')}** ({m.get('name', 'N/A')})")
    else:
        lines.append("\n- No Vertex AI Models found.")

    # 4. Orchestration
    lines.append("\n## 4. Orchestration")
    jobs = load_json(f"{CENSUS_DIR}/orchestration/scheduler_jobs.json")
    if jobs:
        lines.append("\n### Cloud Scheduler Jobs")
        lines.append("| Job Name | Schedule | Target | State |")
        lines.append("|---|---|---|---|")
        for j in jobs:
            target = "HTTP" if 'httpTarget' in j else "AppEngine"
            state = j.get('state', 'UNKNOWN')
            icon = "✅" if state == "ENABLED" else "⏸️"
            name = j.get('name', '').split('/')[-1]
            schedule = j.get('schedule', 'N/A')
            lines.append(f"| `{name}` | `{schedule}` | {target} | {icon} {state} |")
    else:
        lines.append("\n- No Scheduler Jobs found.")
        
    # 5. Firebase
    lines.append("\n## 5. Firebase")
    sites = load_json(f"{CENSUS_DIR}/firebase/hosting_sites.json")
    if sites and 'sites' in sites:
        lines.append("\n### Hosting Sites")
        for s in sites['sites']:
             lines.append(f"- `{s.get('defaultUrl', 'N/A')}` (Type: {s.get('type', 'N/A')})")

    # 6. IAM Summary
    lines.append("\n## 6. IAM & Security")
    sas = load_json(f"{CENSUS_DIR}/iam/service_accounts.json")
    lines.append(f"- **Service Accounts Found**: {len(sas)}")
    secrets = load_json(f"{CENSUS_DIR}/iam/secrets.json")
    lines.append(f"- **Secrets Managed**: {len(secrets)}")


    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Report generated at {REPORT_FILE}")

if __name__ == "__main__":
    generate_markdown()
