"""
System Health Audit Script for InfinityAI.Pro.

This script asynchronously tests and verifies the working status of all
integrated services, including GCP, Firebase, and deployed engine endpoints.

For a detailed overview of the system architecture and components being tested,
please refer to the main documentation at ARCHITECTURE.md.
"""
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
VERTEX_MODEL = "gemini-2.5-pro"

ENGINE_ENDPOINTS = {
    "Engine A (Cloud Run)": os.getenv("ENGINE_A_URL", "https://engine-a-placeholder-url.a.run.app/health"),
    "Engine B (VM)": "http://35.200.135.175:8080/health",
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
        print(f"  {Colors.BLUE}+->{Colors.RESET} {message}")

# --- Health Check Functions ---

def discover_cloud_run_urls(project_id: str, location: str) -> dict:
    """Discovers Cloud Run service URLs for Engine A and C."""
    discovered_urls = {}
    service_names_map = {
        "engine-a": "Engine A (Cloud Run)",
        "engine-c": "Engine C (Cloud Run)",
    }
    
    try:
        from google.cloud import run_v2
        client = run_v2.ServicesClient()
        parent = f"projects/{project_id}/locations/{location}"
        
        print(f"  Discovering Cloud Run services in {location}...")
        services = client.list_services(parent=parent)
        
        found_services = []
        for service in services:
            service_name = service.name.split('/')[-1]
            if service_name in service_names_map:
                engine_key = service_names_map[service_name]
                discovered_urls[engine_key] = f"{service.uri}/health"
                found_services.append(service_name)
        
        if found_services:
             print(f"  +-> Discovered: {', '.join(found_services)}")
        else:
             print(f"  +-> No matching Cloud Run services found in {location}. Using fallbacks.")

    except ImportError:
        print(f"  +-> 'google-cloud-run' not installed. Cannot auto-discover URLs. Using fallbacks.")
    except Exception as e:
        print(f"  +-> Could not discover Cloud Run URLs: {e}. Using fallbacks.")
        
    return discovered_urls


async def check_firestore():
    """Checks Firestore connectivity and read/write operations."""
    service_name = "Firebase/Firestore"
    start_time = time.time()
    try:
        from google.cloud import firestore
        db = firestore.AsyncClient(project=PROJECT_ID)
        
        doc_id = f"health-check-{uuid.uuid4()}"
        doc_ref = db.collection("system_health_checks").document(doc_id)
        
        # Write
        await doc_ref.set({"status": "testing", "timestamp": firestore.SERVER_TIMESTAMP})
        
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

    # Discover Cloud Run URLs and update endpoints
    discovered_urls = discover_cloud_run_urls(PROJECT_ID, "asia-south1")
    ENGINE_ENDPOINTS.update(discovered_urls)
    print() # Add a newline for better formatting

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
        import google.cloud.firestore
        import google.cloud.bigquery
        import google.cloud.storage
        import google.cloud.run_v2
        import vertexai
        import aiohttp
    except ImportError as e:
        print(f"{Colors.RED}Error: Missing dependencies.{Colors.RESET}")
        print("Please install the required libraries by running:")
        print(f"{Colors.YELLOW}pip install google-cloud-firestore google-cloud-bigquery google-cloud-storage google-cloud-aiplatform aiohttp google-cloud-run{Colors.RESET}")
        exit(1)

    # Set credentials if not set
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print(f"{Colors.YELLOW}Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.{Colors.RESET}")
        print("The script will try to use Application Default Credentials (ADC).")
        print("For explicit configuration, set the environment variable to the path of your service account key file.\n")

    asyncio.run(main())
