from google.cloud import logging

client = logging.Client()
print("--- Phase 2: Latency Trace ---")
# Query for recent Engine-B /api/v1/signals/batch logs
query = 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-b" AND httpRequest.requestUrl=~"/api/v1/signals/batch" AND severity>=DEFAULT'
entries = list(client.list_entries(filter_=query, order_by=logging.DESCENDING, max_results=2))
for entry in entries:
    latency = entry.http_request.get('latency', 'unknown') if entry.http_request else 'unknown'
    status = entry.http_request.get('status', 'unknown') if entry.http_request else 'unknown'
    print(f"Engine-B Batch Signal Trace: Status {status}, Latency: {latency}, Timestamp: {entry.timestamp}")

# Query for Engine-A
query_a = 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-a" AND severity>=DEFAULT'
entries_a = list(client.list_entries(filter_=query_a, order_by=logging.DESCENDING, max_results=2))
for entry in entries_a:
    latency = entry.http_request.get('latency', 'unknown') if entry.http_request else 'unknown'
    status = entry.http_request.get('status', 'unknown') if entry.http_request else 'unknown'
    url = entry.http_request.get('requestUrl', 'unknown') if entry.http_request else 'unknown'
    print(f"Engine-A Trace: URL {url}, Status {status}, Latency: {latency}, Timestamp: {entry.timestamp}")

# Query for Engine-C
query_c = 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-c" AND severity>=DEFAULT'
entries_c = list(client.list_entries(filter_=query_c, order_by=logging.DESCENDING, max_results=2))
for entry in entries_c:
    latency = entry.http_request.get('latency', 'unknown') if entry.http_request else 'unknown'
    status = entry.http_request.get('status', 'unknown') if entry.http_request else 'unknown'
    url = entry.http_request.get('requestUrl', 'unknown') if entry.http_request else 'unknown'
    print(f"Engine-C Trace: URL {url}, Status {status}, Latency: {latency}, Timestamp: {entry.timestamp}")


print("\n--- Phase 2: Error Profiling ---")
query_err = 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-c" AND textPayload=~"RL001"'
entries_err = list(client.list_entries(filter_=query_err, order_by=logging.DESCENDING, max_results=5))
print(f"Found {len(entries_err)} RL001 errors in Engine-C.")

print("\n--- Phase 4: Vault Health / Firestore Credentials ---")
query_vault = 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-c" AND textPayload=~"Fetching credentials"'
entries_vault = list(client.list_entries(filter_=query_vault, order_by=logging.DESCENDING, max_results=2))
for entry in entries_vault:
    print(f"Vault Read: {entry.payload} at {entry.timestamp}")
