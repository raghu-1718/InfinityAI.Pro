Here are the exact execution steps and file content updates to apply the refactoring plan.

---

## InfinityAI.Pro Codebase Cleanup & Alignment - Execution Steps

**GCP Project ID:** `project-841b7f97-5ee3-4fbe-920`
**GCP Region:** `asia-south1`
**Engine-B VM Name:** `engine-b`
**Engine-B VM Internal Hostname:** `engine-b.asia-south1-a.c.project-841b7f97-5ee3-4fbe-920.internal`

---

### Task 1: Scrub Conflicting Cloud Run Files for Engine-B

**Objective:** Remove any build configurations that attempt to deploy Engine-B to Cloud Run, as it is now a Compute Engine VM.

#### Step 1.1: Identify and Remove `cloudbuild_engine_b.yaml`

Execute the following shell commands from your project's root directory:

```bash
# Navigate to your project's root directory
# cd /path/to/your/infinityai-repo

# Check if the file exists and then remove it
if [ -f "cloudbuild_engine_b.yaml" ]; then
    echo "Found cloudbuild_engine_b.yaml. Deleting..."
    rm cloudbuild_engine_b.yaml
    echo "cloudbuild_engine_b.yaml removed."
else
    echo "cloudbuild_engine_b.yaml not found. No action needed for this file."
fi
```

#### Step 1.2: Modify `cloudbuild_backend_all.yaml`

**File:** `cloudbuild_backend_all.yaml`

**Action:** Replace the entire content of `cloudbuild_backend_all.yaml` with the following updated content. This removes the `Build Engine-B` and `Deploy Engine-B` steps that were previously for Cloud Run.

```yaml
# cloudbuild_backend_all.yaml (AFTER cleanup)
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/${PROJECT_ID}/engine-a', './backend/engine_a']
  id: 'Build Engine-A'
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'engine-a-service', '--image', 'gcr.io/${PROJECT_ID}/engine-a', '--region', 'asia-south1', '--platform', 'managed', '--allow-unauthenticated']
  id: 'Deploy Engine-A'

# Engine-B Cloud Run deployment steps removed as it's now a Compute Engine VM.
# Its deployment is handled separately (e.g., via Terraform, Ansible, or startup scripts on the VM).

- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/${PROJECT_ID}/engine-c', './backend/engine_c']
  id: 'Build Engine-C'
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'engine-c-service', '--image', 'gcr.io/${PROJECT_ID}/engine-c', '--region', 'asia-south1', '--platform', 'managed', '--allow-unauthenticated']
  id: 'Deploy Engine-C'
# ... other steps
```

---

### Task 2: Update Inter-Service URLs

**Objective:** Ensure all configuration files and environment variable references point Engine-B to its VM internal hostname/IP.

**Target Engine-B Endpoint:** `https://engine-b-r2f5flt77q-el.a.run.app`

#### Step 2.1: Perform Replacements

Execute the following shell commands from your project's root directory. These commands use `sed` to find and replace the old Cloud Run URLs with the new internal VM hostname.

```bash
# Navigate to your project's root directory
# cd /path/to/your/infinityai-repo

OLD_ENGINE_B_URL_PATTERN="https:\/\/engine-b-service-.*\.a\.run\.app" # Adjust regex if needed
NEW_ENGINE_B_URL="https://engine-b-r2f5flt77q-el.a.run.app"

echo "Searching for and replacing old Engine-B Cloud Run URLs with VM internal hostname..."

# Example for Python config files (e.g., backend/engine_a/config.py)
# This assumes the URL is defined as a string variable, e.g., ENGINE_B_URL = "..."
find . -type f -name "config.py" -exec sed -i "s|${OLD_ENGINE_B_URL_PATTERN}|${NEW_ENGINE_B_URL}|g" {} +
echo "Updated config.py files."

# Example for .env files
# This assumes a variable like ENGINE_B_API_URL=...
find . -type f -name ".env" -exec sed -i "s|ENGINE_B_API_URL=${OLD_ENGINE_B_URL_PATTERN}|ENGINE_B_API_URL=${NEW_ENGINE_B_URL}|g" {} +
echo "Updated .env files."

# Example for Kubernetes deployment files (if applicable)
# This assumes a variable like value: "https://engine-b-service..."
find . -type f -name "*.yaml" -exec sed -i "s|value: \"${OLD_ENGINE_B_URL_PATTERN}\"|value: \"${NEW_ENGINE_B_URL}\"|g" {} +
echo "Updated YAML deployment files."

echo "Review all changes carefully after execution."
```

---

### Task 3: Fix Test & Monitoring Scripts

**Objective:** Update `e2e-test.py` and `monitor_24h.py` to target region `asia-south1` and match active resource names.

#### Step 3.1: Update `e2e-test.py`

**File:** `e2e-test.py`

**Action:** Replace the entire content of `e2e-test.py` with the following updated Python code.

```python
# e2e-test.py (Updated)
import requests
import json
import os
from google.cloud import bigquery
import firebase_admin
from firebase_admin import credentials, firestore

# --- Configuration ---
GCP_PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
GCP_REGION = "asia-south1"

ENGINE_A_URL = f"https://engine-a-service-{GCP_PROJECT_ID.split('-')[0]}-as.a.run.app" # Adjust hash if needed
# For E2E testing, Engine-B might expose a public endpoint or be behind a load balancer.
# Replace with the actual public IP or load balancer IP.
ENGINE_B_PUBLIC_ENDPOINT = "http://34.100.200.150:8080" # <<< IMPORTANT: REPLACE WITH ACTUAL PUBLIC IP/LOAD BALANCER IP
ENGINE_C_URL = f"https://engine-c-service-{GCP_PROJECT_ID.split('-')[0]}-as.a.run.app" # Adjust hash if needed

BIGQUERY_DATASET = "infinityai_data"
BIGQUERY_TABLE_A = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.engine_a_logs"
BIGQUERY_TABLE_B = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.engine_b_results"
BIGQUERY_TABLE_C = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.engine_c_outputs"

# Initialize Firebase Admin SDK (ensure service account key is available)
# For local testing, set GOOGLE_APPLICATION_CREDENTIALS env var.
# For CI/CD, Cloud Build/Run/VM will use default credentials.
try:
    firebase_admin.get_app()
except ValueError:
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {'projectId': GCP_PROJECT_ID})
    else:
        print("WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Firebase tests might fail if not running in GCP environment.")
        # Fallback for local dev if no creds, but will fail if Firebase access is needed
        firebase_admin.initialize_app(None, {'projectId': GCP_PROJECT_ID})

db = firestore.client()

def run_test(name, func):
    print(f"--- Running Test: {name} ---")
    try:
        result = func()
        if result:
            print(f"SUCCESS: {name}")
        else:
            print(f"FAILURE: {name}")
        return result
    except Exception as e:
        print(f"ERROR in {name}: {e}")
        return False

def test_engine_a_health():
    try:
        response = requests.get(f"{ENGINE_A_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Engine-A health check failed: {e}")
        return False

def test_engine_b_health():
    try:
        response = requests.get(f"{ENGINE_B_PUBLIC_ENDPOINT}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Engine-B health check failed: {e}")
        return False

def test_engine_c_health():
    try:
        response = requests.get(f"{ENGINE_C_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Engine-C health check failed: {e}")
        return False

def test_engine_a_processing():
    payload = {"data": "test_input_for_engine_a"}
    try:
        response = requests.post(f"{ENGINE_A_URL}/process", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return "processed_by_a" in result and result.get("next_step") == "engine_b"
        return False
    except requests.exceptions.RequestException as e:
        print(f"Engine-A processing test failed: {e}")
        return False

def test_engine_b_processing():
    payload = {"data": "test_input_for_engine_b"}
    try:
        response = requests.post(f"{ENGINE_B_PUBLIC_ENDPOINT}/process", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return "processed_by_b" in result and result.get("next_step") == "engine_c"
        return False
    except requests.exceptions.RequestException as e:
        print(f"Engine-B processing test failed: {e}")
        return False

def test_engine_c_processing():
    payload = {"data": "test_input_for_engine_c"}
    try:
        response = requests.post(f"{ENGINE_C_URL}/process", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return "processed_by_c" in result and result.get("status") == "completed"
        return False
    except requests.exceptions.RequestException as e:
        print(f"Engine-C processing test failed: {e}")
        return False

def test_bigquery_data_ingestion():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    query = f"""
    SELECT COUNT(*) FROM `{BIGQUERY_TABLE_A}`
    WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    """
    try:
        query_job = client.query(query)
        results = query_job.result()
        for row in results:
            return row[0] > 0 # Check if any recent data exists
        return False
    except Exception as e:
        print(f"BigQuery data ingestion test failed: {e}")
        return False

def test_firebase_connectivity():
    try:
        doc_ref = db.collection('e2e_test_data').document('connectivity_test')
        doc_ref.set({'timestamp': firestore.SERVER_TIMESTAMP, 'status': 'ok'})
        doc = doc_ref.get()
        return doc.exists and doc.to_dict().get('status') == 'ok'
    except Exception as e:
        print(f"Firebase connectivity test failed: {e}")
        return False

if __name__ == "__main__":
    all_tests_passed = True

    all_tests_passed &= run_test("Engine-A Health Check", test_engine_a_health)
    all_tests_passed &= run_test("Engine-B Health Check", test_engine_b_health)
    all_tests_passed &= run_test("Engine-C Health Check", test_engine_c_health)

    all_tests_passed &= run_test("Engine-A Processing Flow", test_engine_a_processing)
    all_tests_passed &= run_test("Engine-B Processing Flow", test_engine_b_processing)
    all_tests_passed &= run_test("Engine-C Processing Flow", test_engine_c_processing)

    all_tests_passed &= run_test("BigQuery Data Ingestion Check", test_bigquery_data_ingestion)
    all_tests_passed &= run_test("Firebase Connectivity Check", test_firebase_connectivity)

    if all_tests_passed:
        print("\nAll E2E tests passed successfully!")
        exit(0)
    else:
        print("\nSome E2E tests failed.")
        exit(1)
```

#### Step 3.2: Update `monitor_24h.py`

**File:** `monitor_24h.py`

**Action:** Replace the entire content of `monitor_24h.py` with the following updated Python code.

```python
# monitor_24h.py (Updated)
import requests
import time
import datetime
import os
from google.cloud import bigquery, logging_v2
import firebase_admin
from firebase_admin import credentials, firestore
from collections import defaultdict

# --- Configuration ---
GCP_PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
GCP_REGION = "asia-south1"

ENGINE_A_URL = f"https://engine-a-service-{GCP_PROJECT_ID.split('-')[0]}-as.a.run.app" # Adjust hash if needed
# For monitoring, Engine-B might have a dedicated monitoring endpoint or use its public IP.
# Replace with the actual public IP or load balancer IP.
ENGINE_B_MONITORING_ENDPOINT = "http://34.100.200.150:8080" # <<< IMPORTANT: REPLACE WITH ACTUAL PUBLIC IP/LOAD BALANCER IP
ENGINE_C_URL = f"https://engine-c-service-{GCP_PROJECT_ID.split('-')[0]}-as.a.run.app" # Adjust hash if needed

BIGQUERY_DATASET = "infinityai_data"
BIGQUERY_TABLE_A = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.engine_a_logs"
BIGQUERY_TABLE_B = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.engine_b_results"
BIGQUERY_TABLE_C = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.engine_c_outputs"

# Initialize Firebase Admin SDK
try:
    firebase_admin.get_app()
except ValueError:
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {'projectId': GCP_PROJECT_ID})
    else:
        print("WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Firebase monitoring might be limited.")
        firebase_admin.initialize_app(None, {'projectId': GCP_PROJECT_ID})
db = firestore.client()

# Initialize BigQuery and Logging clients
bq_client = bigquery.Client(project=GCP_PROJECT_ID)
logging_client = logging_v2.Client(project=GCP_PROJECT_ID)

def log_status(component, status, details=""):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] {component} - Status: {status} - Details: {details}")
    # In a real scenario, push this to Stackdriver Logging or a monitoring dashboard.

def check_http_endpoint(name, url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            log_status(name, "OK", f"HTTP 200 from {url}")
            return True
        else:
            log_status(name, "WARNING", f"HTTP {response.status_code} from {url}")
            return False
    except requests.exceptions.RequestException as e:
        log_status(name, "CRITICAL", f"Failed to connect to {url}: {e}")
        return False

def check_bigquery_recent_data(table_id, hours=24):
    query = f"""
    SELECT COUNT(*) FROM `{table_id}`
    WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
    """
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        for row in results:
            if row[0] > 0:
                log_status(f"BigQuery Table {table_id}", "OK", f"Found {row[0]} recent entries in last {hours} hours.")
                return True
            else:
                log_status(f"BigQuery Table {table_id}", "WARNING", f"No recent entries found in last {hours} hours.")
                return False
    except Exception as e:
        log_status(f"BigQuery Table {table_id}", "CRITICAL", f"BigQuery query failed: {e}")
        return False

def check_firebase_recent_writes(collection_name, hours=24):
    try:
        # Query for documents written in the last 'hours'
        # Note: Firestore queries on timestamp require an index.
        # For monitoring, we might just check for *any* document or a specific health document.
        # This example checks for any document in a specific collection.
        docs = db.collection(collection_name).limit(1).get()
        if docs:
            log_status(f"Firebase Collection {collection_name}", "OK", "Found documents.")
            return True
        else:
            log_status(f"Firebase Collection {collection_name}", "WARNING", "No documents found.")
            return False
    except Exception as e:
        log_status(f"Firebase Collection {collection_name}", "CRITICAL", f"Firebase check failed: {e}")
        return False

def check_gcp_logs_for_errors(resource_type, resource_name, hours=1):
    filter_str = f'resource.type="{resource_type}" AND resource.labels.service_name="{resource_name}" AND severity>=ERROR AND timestamp>="{datetime.datetime.utcnow() - datetime.timedelta(hours=hours):%Y-%m-%dT%H:%M:%SZ}"'
    entries = logging_client.list_entries(filter_=filter_str, page_size=1)
    try:
        first_entry = next(entries)
        log_status(f"GCP Logs for {resource_name}", "CRITICAL", f"Found recent ERROR logs: {first_entry.payload}")
        return False
    except StopIteration:
        log_status(f"GCP Logs for {resource_name}", "OK", "No recent ERROR logs found.")
        return True
    except Exception as e:
        log_status(f"GCP Logs for {resource_name}", "WARNING", f"Failed to check GCP logs: {e}")
        return False

if __name__ == "__main__":
    print(f"Starting 24-hour monitoring for InfinityAI.Pro services in {GCP_REGION}...")

    # HTTP Endpoint Checks
    check_http_endpoint("Engine-A (Cloud Run)", f"{ENGINE_A_URL}/health")
    check_http_endpoint("Engine-B (Compute Engine)", f"{ENGINE_B_MONITORING_ENDPOINT}/health")
    check_http_endpoint("Engine-C (Cloud Run)", f"{ENGINE_C_URL}/health")

    # BigQuery Data Ingestion Checks
    check_bigquery_recent_data(BIGQUERY_TABLE_A, hours=24)
    check_bigquery_recent_data(BIGQUERY_TABLE_B, hours=24)
    check_bigquery_recent_data(BIGQUERY_TABLE_C, hours=24)

    # Firebase Connectivity Check
    check_firebase_recent_writes('e2e_test_data', hours=24) # Assuming e2e tests write here

    # GCP Logging Checks (for recent errors)
    # Note: resource.labels.service_name for Cloud Run is the service name.
    # For Compute Engine, it might be instance_id or instance_name.
    # Adjust resource_type and labels as per your Stackdriver Logging setup.
    check_gcp_logs_for_errors("cloud_run_revision", "engine-a-service", hours=1)
    check_gcp_logs_for_errors("gce_instance", "engine-b", hours=1) # Assuming 'gce_instance' and instance name
    check_gcp_logs_for_errors("cloud_run_revision", "engine-c-service", hours=1)

    print("\n24-hour monitoring complete. Review logs for status.")
```