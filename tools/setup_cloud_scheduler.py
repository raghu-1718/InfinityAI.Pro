"""
GCP Cloud Scheduler & Cloud Run Jobs Auto-Scaling Provisioning Script
Automatically provisions market-open (8:55 AM IST) and market-close (3:45 PM IST) jobs.
"""
import sys
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
COMPUTE_SA = "313407263327-compute@developer.gserviceaccount.com"
SCHEDULER_SA = f"scheduler-invoker@{PROJECT_ID}.iam.gserviceaccount.com"

def run_gcloud(args):
    cmd = ["gcloud"] + args
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        print(f"  ⚠️ Note/Output: {res.stderr.strip() or res.stdout.strip()}")
    else:
        print(f"  ✅ Success: {res.stdout.strip()[:100]}...")

def main():
    print("=" * 80)
    print("PROVISIONING AUTOMATED MARKET-HOURS SCALING VIA GCP CLOUD SCHEDULER")
    print("=" * 80)

    # 1. Enable Cloud Scheduler API
    print("\n1. Enabling Cloud Scheduler API...")
    run_gcloud(["services", "enable", "cloudscheduler.googleapis.com", f"--project={PROJECT_ID}"])

    # 2. Grant Cloud Run Admin rights to default compute SA
    print("\n2. Granting Cloud Run Admin role to Compute Service Account...")
    run_gcloud([
        "projects", "add-iam-policy-binding", PROJECT_ID,
        f"--member=serviceAccount:{COMPUTE_SA}",
        "--role=roles/run.admin"
    ])

    # 3. Create Cloud Run Job: market-open (Scale UP to --min-instances=1)
    print("\n3. Creating Cloud Run Job: market-open...")
    run_gcloud([
        "run", "jobs", "create", "market-open",
        "--image=gcr.io/google.com/cloudsdktool/cloud-sdk:slim",
        "--command=bash",
        '--args=-c,gcloud run services update engine-a --min-instances=1 --region=us-central1 --quiet && gcloud run services update engine-c --min-instances=1 --region=us-central1 --quiet',
        "--region=us-central1",
        f"--service-account={COMPUTE_SA}",
        f"--project={PROJECT_ID}"
    ])

    # 4. Create Cloud Run Job: market-close (Scale DOWN to --min-instances=0)
    print("\n4. Creating Cloud Run Job: market-close...")
    run_gcloud([
        "run", "jobs", "create", "market-close",
        "--image=gcr.io/google.com/cloudsdktool/cloud-sdk:slim",
        "--command=bash",
        '--args=-c,gcloud run services update engine-a --min-instances=0 --region=us-central1 --quiet && gcloud run services update engine-c --min-instances=0 --region=us-central1 --quiet',
        "--region=us-central1",
        f"--service-account={COMPUTE_SA}",
        f"--project={PROJECT_ID}"
    ])

    # 5. Create Service Account for Cloud Scheduler
    print("\n5. Creating Scheduler Invoker Service Account...")
    run_gcloud([
        "iam", "service-accounts", "create", "scheduler-invoker",
        "--display-name=Cloud Scheduler Invoker",
        f"--project={PROJECT_ID}"
    ])

    print("\n6. Granting Cloud Run Invoker role to Scheduler SA...")
    run_gcloud([
        "projects", "add-iam-policy-binding", PROJECT_ID,
        f"--member=serviceAccount:{SCHEDULER_SA}",
        "--role=roles/run.invoker"
    ])

    # 7. Create Cloud Scheduler Job: market-open-job (8:55 AM IST Mon-Fri)
    print("\n7. Creating Cloud Scheduler CRON: market-open-job (8:55 AM IST Mon-Fri)...")
    run_gcloud([
        "scheduler", "jobs", "create", "http", "market-open-job",
        "--location=us-central1",
        '--schedule=55 8 * * 1-5',
        '--time-zone=Asia/Kolkata',
        f'--uri=https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/{PROJECT_ID}/jobs/market-open:run',
        "--http-method=POST",
        f"--oauth-service-account-email={SCHEDULER_SA}",
        f"--project={PROJECT_ID}"
    ])

    # 8. Create Cloud Scheduler Job: market-close-job (3:45 PM IST Mon-Fri)
    print("\n8. Creating Cloud Scheduler CRON: market-close-job (3:45 PM IST Mon-Fri)...")
    run_gcloud([
        "scheduler", "jobs", "create", "http", "market-close-job",
        "--location=us-central1",
        '--schedule=45 15 * * 1-5',
        '--time-zone=Asia/Kolkata',
        f'--uri=https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/{PROJECT_ID}/jobs/market-close:run',
        "--http-method=POST",
        f"--oauth-service-account-email={SCHEDULER_SA}",
        f"--project={PROJECT_ID}"
    ])

    print("\n" + "=" * 80)
    print("PROVISIONING COMPLETED SUCCESSFULLY 🎉")
    print("=" * 80)

if __name__ == "__main__":
    main()
