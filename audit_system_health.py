import asyncio
import time
import os
import aiohttp
import uuid

# --- Configuration ---
PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
GCS_BUCKET = "infinity-ai-models-vault"
BQ_DATASET = "market_data"
BQ_TABLE = "options_ticks"
VERTEX_LOCATION = "us-central1"
VERTEX_MODEL = "gemini-1.0-pro"

ENGINE_ENDPOINTS = {
    "Engine A (Cloud Run)": os.getenv("ENGINE_A_URL", "https://engine-a-placeholder-url.a.run.app/health"),
    "Engine B (VM)": "http://35.200.135.175:8000/health",
    "Engine C (Cloud Run)": os.getenv("ENGINE_C_URL", "https://engine-c-placeholder-url.a.run.app/health"),
}

# --- Color Codes ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(service, status, latency, message):
    status_color = {
        "OK": Colors.GREEN,
        "FAILED": Colors.RED,
        "WARNING": Colors.YELLOW,
    }.get(status, Colors.RESET)

    print(f"{Colors.BOLD}{service:<25}{Colors.RESET} [{status_color}{status:^8}{Colors.RESET}] ({latency:7.2f} ms)")
    if message:
        print(f"  {Colors.BLUE}└─>{Colors.RESET} {message}")

# --- Health Check Functions ---

async def check_firestore():
    """Checks Firestore connectivity and read/write operations."""
    service_name = "Firebase/Firestore"
    start_time = time.time()
    try:
        from google.cloud import firestore_async
        db = firestore_async.client.AsyncClient(project=PROJECT_ID)
        
        doc_id = f"health-check-{uuid.uuid4()}"
        doc_ref = db.collection("system_health_checks").document(doc_id)
        
        # Write
        await doc_ref.set({"status": "testing", "timestamp": firestore_async.SERVER_TIMESTAMP})
        
        # Read
        doc = await doc_ref.get()
        if not doc.exists:
            raise Exception("Test document not found after writing.")
            
        # Delete
        await doc_ref.delete()
        
        latency = (time.time() - start_time) * 1000
        return service_name, "OK", latency, "Read/write test successful."
    except ImportError:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, "google-cloud-firestore not installed. Run 'pip install google-cloud-firestore'."
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, f"Error: {e}. Check credentials (GOOGLE_APPLICATION_CREDENTIALS) and permissions."

async def check_bigquery():
    """Checks BigQuery connectivity and query execution."""
    service_name = "Google BigQuery"
    start_time = time.time()
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID)
        
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`"
        
        query_job = client.query(query)
        results = query_job.result() # Waits for job to complete
        
        row_count = list(results)[0].count
        
        latency = (time.time() - start_time) * 1000
        return service_name, "OK", latency, f"Successfully queried table, found {row_count} rows."
    except ImportError:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, "google-cloud-bigquery not installed. Run 'pip install google-cloud-bigquery'."
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, f"Error: {e}. Check permissions for project '{PROJECT_ID}'."

async def check_vertex_ai():
    """Checks Vertex AI/Gemini model inference."""
    service_name = "Vertex AI (Gemini)"
    start_time = time.time()
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=PROJECT_ID, location=VERTEX_LOCATION)
        model = GenerativeModel(VERTEX_MODEL)
        
        response = await model.generate_content_async("Ping")
        
        if not response.text:
            raise Exception("Received empty response from model.")
            
        latency = (time.time() - start_time) * 1000
        return service_name, "OK", latency, f"Model responded successfully. Response: '{response.text.strip()}'"
    except ImportError:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, "google-cloud-aiplatform not installed. Run 'pip install google-cloud-aiplatform'."
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, f"Error: {e}. Check Vertex AI API is enabled and you have permissions."

async def check_cloud_storage():
    """Checks Cloud Storage bucket accessibility."""
    service_name = "Google Cloud Storage"
    start_time = time.time()
    try:
        from google.cloud import storage
        client = storage.Client(project=PROJECT_ID)
        
        bucket = client.get_bucket(GCS_BUCKET)
        
        if not bucket.exists():
             raise Exception(f"Bucket '{GCS_BUCKET}' does not exist.")

        latency = (time.time() - start_time) * 1000
        return service_name, "OK", latency, f"Successfully accessed bucket '{GCS_BUCKET}'."
    except ImportError:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, "google-cloud-storage not installed. Run 'pip install google-cloud-storage'."
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return service_name, "FAILED", latency, f"Error: {e}. Check bucket name and permissions."

async def check_engine_health(name, url):
    """Checks the health of a deployed engine via its HTTP endpoint."""
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                latency = (time.time() - start_time) * 1000
                if response.status == 200:
                    try:
                        data = await response.json()
                        version = data.get('version', 'N/A')
                        return name, "OK", latency, f"Responded with status {response.status}. Version: {version}"
                    except Exception:
                        return name, "OK", latency, f"Responded with status {response.status}, but response is not valid JSON."
                else:
                    if name == "Engine B (VM)" and response.status == 404:
                         return name, "FAILED", latency, f"Endpoint returned {response.status} Not Found. The URL may be incorrect. Try '/healthz' or '/api/health'."
                    return name, "FAILED", latency, f"Endpoint returned status {response.status}."
    except aiohttp.ClientConnectorError as e:
        latency = (time.time() - start_time) * 1000
        return name, "FAILED", latency, f"Connection error: {e}. Check URL and network."
    except asyncio.TimeoutError:
        latency = (time.time() - start_time) * 1000
        return name, "FAILED", latency, "Request timed out after 10 seconds."
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return name, "FAILED", latency, f"An unexpected error occurred: {e}"

# --- Main Orchestrator ---

async def main():
    """Runs all health checks and prints a report."""
    print(f"{Colors.BOLD}--- InfinityAI System Health Audit ---{Colors.RESET}")
    print(f"Project: {Colors.YELLOW}{PROJECT_ID}{Colors.RESET}, Time: {time.ctime()}\n")

    tasks = [
        check_firestore(),
        check_bigquery(),
        check_vertex_ai(),
        check_cloud_storage(),
    ]
    
    for name, url in ENGINE_ENDPOINTS.items():
        tasks.append(check_engine_health(name, url))

    results = await asyncio.gather(*tasks)
    
    failures = []
    for res in results:
        print_status(*res)
        if res[1] != "OK":
            failures.append(res)
            
    print(f"\n{Colors.BOLD}--- Summary & Required Fixes ---{Colors.RESET}")
    if not failures:
        print(f"{Colors.GREEN}✅ All systems are operational.{Colors.RESET}")
    else:
        print(f"{Colors.RED}Found {len(failures)} issue(s) that require attention:{Colors.RESET}")
        for i, (service, status, _, message) in enumerate(failures):
            print(f"  {i+1}. {Colors.BOLD}{service}{Colors.RESET}: {Colors.RED}{message}{Colors.RESET}")

if __name__ == "__main__":
    # Check for dependencies
    try:
        import google.cloud.firestore_async
        import google.cloud.bigquery
        import google.cloud.storage
        import vertexai
        import aiohttp
    except ImportError as e:
        print(f"{Colors.RED}Error: Missing dependencies.{Colors.RESET}")
        print("Please install the required libraries by running:")
        print(f"{Colors.YELLOW}pip install google-cloud-firestore google-cloud-bigquery google-cloud-storage google-cloud-aiplatform aiohttp{Colors.RESET}")
        exit(1)

    # Set credentials if not set
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print(f"{Colors.YELLOW}Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.{Colors.RESET}")
        print("The script will try to use Application Default Credentials (ADC).")
        print("For explicit configuration, set the environment variable to the path of your service account key file.\n")

    asyncio.run(main())
