"""
Production GCP Cloud Logging Audit Script (Past 72+ Hours)
Queries gcloud logging for project-841b7f97-5ee3-4fbe-920 across Engine A, Engine B, Engine C.
"""
import sys
import os
import json
import subprocess
from datetime import datetime, timedelta

def audit_cloud_logging():
    print("=" * 80)
    print("GCP CLOUD LOGGING PRODUCTION TRAFFIC AUDIT (PAST 72+ HOURS)")
    print("=" * 80)

    # 4 days ago timestamp
    four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%dT00:00:00Z")
    
    filter_expr = f'resource.type="cloud_run_revision" AND timestamp>="{four_days_ago}"'
    cmd = [
        "gcloud", "logging", "read",
        filter_expr,
        "--project=project-841b7f97-5ee3-4fbe-920",
        "--limit=500",
        "--format=json"
    ]

    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
        logs = json.loads(out)
        print(f"Total Log Records Retreived: {len(logs)}")
    except Exception as e:
        print(f"Error querying GCP Cloud Logging: {e}")
        return

    service_counts = {}
    status_codes = {}
    severities = {}
    latencies = []
    dhan_postback_events = 0
    signal_eval_events = 0

    for log in logs:
        # Extract Service Name
        labels = log.get("resource", {}).get("labels", {})
        svc = labels.get("service_name", "unknown")
        service_counts[svc] = service_counts.get(svc, 0) + 1

        # Extract Severity
        sev = log.get("severity", "DEFAULT")
        severities[sev] = severities.get(sev, 0) + 1

        # Extract HTTP Request Payload
        httpRequest = log.get("httpRequest", {})
        if httpRequest:
            status = httpRequest.get("status")
            if status:
                status_codes[status] = status_codes.get(status, 0) + 1
            
            latency_str = httpRequest.get("latency", "")
            if latency_str.endswith("s"):
                try:
                    lat_sec = float(latency_str[:-1])
                    latencies.append(lat_sec)
                except ValueError:
                    pass

        # Text Payload Audit
        text_payload = log.get("textPayload", "")
        json_payload = log.get("jsonPayload", {})
        msg = text_payload or str(json_payload)

        if "postback" in msg.lower() or "dhan" in msg.lower():
            dhan_postback_events += 1
        if "signal" in msg.lower() or "gemini" in msg.lower():
            signal_eval_events += 1

    print("\n--- 1. Cloud Run Service Traffic Distribution ---")
    for svc, count in service_counts.items():
        print(f"  - {svc}: {count} log entries")

    print("\n--- 2. HTTP Status Code Breakdown ---")
    for st, count in sorted(status_codes.items()):
        print(f"  - HTTP {st}: {count} requests")

    print("\n--- 3. Severity Distribution ---")
    for sev, count in severities.items():
        print(f"  - {sev}: {count} entries")

    if latencies:
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p90 = latencies[int(len(latencies) * 0.90)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg_lat = sum(latencies) / len(latencies)
        print("\n--- 4. Latency Distribution (Seconds) ---")
        print(f"  - Average: {avg_lat:.3f}s")
        print(f"  - P50 (Median): {p50:.3f}s")
        print(f"  - P90: {p90:.3f}s")
        print(f"  - P99: {p99:.3f}s")

    print("\n--- 5. Key Operational Events ---")
    print(f"  - DhanHQ API & Webhook Log Events: {dhan_postback_events}")
    print(f"  - Gemini & AI Signal Generation Events: {signal_eval_events}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    audit_cloud_logging()
