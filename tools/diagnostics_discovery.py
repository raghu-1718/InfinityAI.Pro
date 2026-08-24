"""
InfinityAI.Pro - Live Diagnostic Discovery Tool
Performs deep discovery across GCP, Firebase, Cloud Run, Compute Engine, Pub/Sub, BigQuery, and Schedulers.
"""
import subprocess
import json
import os
import sys

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"

def run_json_cmd(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True, shell=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            return json.loads(res.stdout)
        except Exception:
            return {"raw": res.stdout}
    return {"error": res.stderr.strip() if res.stderr else "empty response"}

def main():
    report = {
        "project_id": PROJECT_ID,
        "cloud_run": [],
        "compute_engine": [],
        "pubsub_topics": [],
        "pubsub_subscriptions": [],
        "bigquery_datasets": [],
        "schedulers": []
    }

    # 1. Cloud Run
    print("Querying Cloud Run services...")
    cr_data = run_json_cmd(f"gcloud run services list --project={PROJECT_ID} --format=json")
    if isinstance(cr_data, list):
        for s in cr_data:
            report["cloud_run"].append({
                "name": s.get("metadata", {}).get("name"),
                "region": s.get("metadata", {}).get("labels", {}).get("cloud.googleapis.com/location", "unknown"),
                "url": s.get("status", {}).get("url"),
                "image": s.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("image"),
                "concurrency": s.get("spec", {}).get("template", {}).get("spec", {}).get("containerConcurrency"),
                "timeout": s.get("spec", {}).get("template", {}).get("spec", {}).get("timeoutSeconds"),
                "resources": s.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("resources", {}),
                "traffic": s.get("status", {}).get("traffic", [])
            })

    # 2. Compute Engine VMs
    print("Querying Compute Engine VMs...")
    ce_data = run_json_cmd(f"gcloud compute instances list --project={PROJECT_ID} --format=json")
    if isinstance(ce_data, list):
        for v in ce_data:
            report["compute_engine"].append({
                "name": v.get("name"),
                "zone": v.get("zone", "").split("/")[-1],
                "machine_type": v.get("machineType", "").split("/")[-1],
                "status": v.get("status"),
                "internal_ip": v.get("networkInterfaces", [{}])[0].get("networkIP"),
                "nat_ip": v.get("networkInterfaces", [{}])[0].get("accessConfigs", [{}])[0].get("natIP")
            })

    # 3. Pub/Sub Topics & Subscriptions
    print("Querying Pub/Sub Topics & Subscriptions...")
    topics_data = run_json_cmd(f"gcloud pubsub topics list --project={PROJECT_ID} --format=json")
    subs_data = run_json_cmd(f"gcloud pubsub subscriptions list --project={PROJECT_ID} --format=json")
    if isinstance(topics_data, list):
        report["pubsub_topics"] = [t.get("name") for t in topics_data]
    if isinstance(subs_data, list):
        report["pubsub_subscriptions"] = [{
            "name": s.get("name"),
            "topic": s.get("topic"),
            "ack_deadline_seconds": s.get("ackDeadlineSeconds"),
            "push_config": s.get("pushConfig", {})
        } for s in subs_data]

    # 4. BigQuery Datasets
    print("Querying BigQuery Datasets...")
    bq_data = run_json_cmd(f"bq ls --project_id={PROJECT_ID} --format=prettyjson")
    if isinstance(bq_data, list):
        report["bigquery_datasets"] = [b.get("datasetReference", {}).get("datasetId") for b in bq_data]

    # 5. Cloud Schedulers
    print("Querying Cloud Schedulers in asia-south1...")
    sched_data = run_json_cmd(f"gcloud scheduler jobs list --project={PROJECT_ID} --location=asia-south1 --format=json")
    if isinstance(sched_data, list):
        for j in sched_data:
            report["schedulers"].append({
                "name": j.get("name", "").split("/")[-1],
                "schedule": j.get("schedule"),
                "timezone": j.get("timeZone"),
                "state": j.get("state"),
                "target": j.get("httpTarget", {}).get("uri") or j.get("pubsubTarget", {}).get("topicName")
            })

    out_file = os.path.join(os.path.dirname(__file__), "live_diagnostic_report.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[OK] Diagnostic discovery completed and saved to {out_file}")
    print(f"Cloud Run Services: {len(report['cloud_run'])}")
    print(f"Compute Engine VMs: {len(report['compute_engine'])}")
    print(f"Pub/Sub Topics: {len(report['pubsub_topics'])} | Subscriptions: {len(report['pubsub_subscriptions'])}")
    print(f"BigQuery Datasets: {report['bigquery_datasets']}")
    print(f"Cloud Schedulers: {len(report['schedulers'])}")

if __name__ == "__main__":
    main()
