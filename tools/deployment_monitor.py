import subprocess
import time
import sys
import json
from datetime import datetime

SERVICES = ["engine-a", "engine-b"]
REGION = "us-central1"

def get_latest_revision(service):
    try:
        cmd = [
            "gcloud", "run", "revisions", "list",
            "--service", service,
            "--region", REGION,
            "--format=json",
            "--limit=1"
        ]
        # On Windows, shell=True is often needed for batch/cmd files like gcloud.cmd
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        data = json.loads(result.stdout)
        if not data:
            return None
        return data[0]
    except Exception as e:
        print(f"Error fetching revision for {service}: {e}")
        return None

def parse_creation_time(rev):
    # Format: 2026-01-23T11:38:11.666675Z or similar
    ts_str = rev['metadata']['creationTimestamp']
    # Handle fractional seconds if present
    ts_str = ts_str.replace("Z", "+00:00")
    return datetime.fromisoformat(ts_str)

def monitor():
    print(f"Starting deployment monitor for: {', '.join(SERVICES)}")
    print(f"Current Time: {datetime.now().isoformat()}")
    
    # Store initial latest revisions to compare against
    initial_revisions = {}
    for svc in SERVICES:
        rev = get_latest_revision(svc)
        if rev:
            initial_revisions[svc] = rev['metadata']['name']
            print(f"[{svc}] Current Latest: {rev['metadata']['name']} ({rev['metadata']['creationTimestamp']})")
    
    start_time = time.time()
    timeout = 900 # 15 minutes
    
    completed = set()
    
    while time.time() - start_time < timeout:
        if len(completed) == len(SERVICES):
            print("\n✅ All services have new revisions!")
            return True
            
        print(".", end="", flush=True)
        time.sleep(30)
        
        for svc in SERVICES:
            if svc in completed:
                continue
                
            rev = get_latest_revision(svc)
            if not rev:
                continue
                
            rev_name = rev['metadata']['name']
            
            # Check if this is a new revision
            if svc in initial_revisions and rev_name != initial_revisions[svc]:
                # New revision detected!
                # Check if it is ready/active
                status_conds = rev.get('status', {}).get('conditions', [])
                is_ready = False
                for cond in status_conds:
                    if cond['type'] == 'Ready' and cond['status'] == 'True':
                        is_ready = True
                        break
                
                print(f"\n[{svc}] New Revision Detected: {rev_name}")
                if is_ready:
                    print(f"[{svc}] ✅ Revision is READY/ACTIVE.")
                    completed.add(svc)
                else:
                    print(f"[{svc}] ⏳ Revision is processing...")
            
            # If we didn't have an initial revision (first deploy), logic is slightly different but assuming update here
            
    print("\n❌ Timeout waiting for deployment.")
    return False

if __name__ == "__main__":
    success = monitor()
    sys.exit(0 if success else 1)
