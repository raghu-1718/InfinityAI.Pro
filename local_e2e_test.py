import subprocess
import time
import requests
import sys

def check_health(url):
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False

import os
env = os.environ.copy()
env["PYTHONPATH"] = "c:/Users/Raghu/Projects/InfinityAI.Pro/backend"

print("Starting Engine A...")
pA = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8001"], cwd="c:/Users/Raghu/Projects/InfinityAI.Pro/backend/engine-a", env=env)
print("Starting Engine B...")
pB = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8002"], cwd="c:/Users/Raghu/Projects/InfinityAI.Pro/backend/engine-b", env=env)
print("Starting Engine C...")
pC = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8003"], cwd="c:/Users/Raghu/Projects/InfinityAI.Pro/backend/engine-c", env=env)

print("Waiting for engines to start...")
time.sleep(10)

success = True
for name, port in [("Engine A", 8001), ("Engine B", 8002), ("Engine C", 8003)]:
    url = f"http://localhost:{port}/health"
    if check_health(url):
        print(f"✅ {name} is UP at {url}")
    else:
        print(f"❌ {name} is DOWN at {url}")
        success = False

if success:
    print("\nRunning integration checks...")
    try:
        # Check Engine C Dhan API
        res = requests.get("http://localhost:8003/api/dhan/status")
        print("Engine C Dhan Status:", res.json() if res.status_code == 200 else res.status_code)
    except Exception as e:
        print("Engine C check failed:", e)

# Terminate
print("\nTerminating engines...")
pA.terminate()
pB.terminate()
pC.terminate()
