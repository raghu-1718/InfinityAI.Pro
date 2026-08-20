"""
InfinityAI.Pro — Vertex AI Nightly Retraining Pipeline
======================================================
Engine B | Engine-Grade: Production | Version: 1.0.0

Cloud Scheduler → Pub/Sub → Cloud Run trigger → Vertex AI Custom Job
Schedule: 18:00 IST (12:30 UTC) every weekday — after NSE close

Setup command (run once):
    python setup_nightly_retrain.py --project <PROJECT_ID>

Architecture:
    Cloud Scheduler (nightly 18:00 IST)
      ↓ triggers
    Pub/Sub topic `model-retrain-trigger`
      ↓ pushes to
    Engine B /api/v1/training/trigger endpoint
      ↓ submits
    Vertex AI Custom Job (n1-standard-4)
      ↓ trains
    9-Model Ensemble → GCS Model Vault
      ↓ hot-reloads
    Engine B MLModelManager

Cost: ~₹120 per training run × 5 symbols = ~₹600/night
"""

import os
import json
import argparse
import logging
from datetime import datetime

logger = logging.getLogger("InfinityAI.VertexPipelineSetup")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")

PROJECT_ID   = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
REGION       = "asia-south1"
SCHEDULER_TZ = "Asia/Kolkata"
SYMBOLS      = ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY", "MIDCPNIFTY"]

PUBSUB_TOPIC     = "model-retrain-trigger"
PUBSUB_DRIFT     = "model-drift-alerts"
SCHEDULER_NAME   = "infinity-nightly-retrain"
ENGINE_B_URL     = os.getenv("ENGINE_B_URL", "https://engine-b-ml-prod.asia-south1.run.app")


def create_pubsub_topics() -> None:
    """Create required Pub/Sub topics if they don't exist."""
    from google.cloud import pubsub_v1
    publisher = pubsub_v1.PublisherClient()

    for topic_name in [PUBSUB_TOPIC, PUBSUB_DRIFT]:
        topic_path = publisher.topic_path(PROJECT_ID, topic_name)
        try:
            publisher.create_topic(request={"name": topic_path})
            logger.info(f"✅ Pub/Sub topic created: {topic_path}")
        except Exception as e:
            if "ALREADY_EXISTS" in str(e) or "409" in str(e):
                logger.info(f"ℹ️ Pub/Sub topic already exists: {topic_name}")
            else:
                logger.warning(f"Topic creation failed {topic_name}: {e}")


def create_cloud_scheduler_jobs() -> None:
    """
    Create Cloud Scheduler jobs for nightly retraining.
    One job per symbol, staggered by 10 minutes to avoid concurrent Vertex quotas.
    """
    from google.cloud import scheduler_v1

    client   = scheduler_v1.CloudSchedulerClient()
    parent   = f"projects/{PROJECT_ID}/locations/{REGION}"

    for i, symbol in enumerate(SYMBOLS):
        # Stagger: 18:00, 18:10, 18:20, 18:30, 18:40 IST
        hour   = 18
        minute = i * 10
        cron   = f"{minute} {hour} * * 1-5"  # Mon-Fri

        job_id   = f"infinity-retrain-{symbol.lower()}"
        job_name = f"{parent}/jobs/{job_id}"

        # HTTP target: POST to Engine B trigger endpoint
        body = json.dumps({"symbol": symbol, "days": 730}).encode("utf-8")
        http_target = scheduler_v1.HttpTarget(
            uri=f"{ENGINE_B_URL}/api/v1/training/trigger?symbol={symbol}&days=730",
            http_method=scheduler_v1.HttpMethod.POST,
            body=body,
            headers={"Content-Type": "application/json"},
            oidc_token=scheduler_v1.OidcToken(
                service_account_email=f"engine-b-sa@{PROJECT_ID}.iam.gserviceaccount.com",
                audience=ENGINE_B_URL,
            ),
        )

        job = scheduler_v1.Job(
            name=job_name,
            schedule=cron,
            time_zone=SCHEDULER_TZ,
            http_target=http_target,
            description=f"InfinityAI.Pro — Nightly {symbol} 9-model retrain at 18:{minute:02d} IST",
            attempt_deadline={"seconds": 7200},  # 2-hour timeout for training
        )

        try:
            created_job = client.create_job(
                request=scheduler_v1.CreateJobRequest(parent=parent, job=job)
            )
            logger.info(f"✅ Scheduler job created: {created_job.name} | cron: {cron}")
        except Exception as e:
            if "ALREADY_EXISTS" in str(e):
                # Update existing
                try:
                    client.update_job(request=scheduler_v1.UpdateJobRequest(job=job))
                    logger.info(f"✅ Scheduler job updated: {job_name}")
                except Exception as ue:
                    logger.warning(f"Scheduler update failed: {ue}")
            else:
                logger.error(f"Scheduler job creation failed for {symbol}: {e}")


def setup_vertex_service_account() -> None:
    """
    Grant Engine B service account the required IAM roles for Vertex AI job submission.
    Roles needed:
      - roles/aiplatform.user (submit training jobs)
      - roles/storage.objectAdmin (on GCS Model Vault)
      - roles/bigquery.dataEditor (for feature store + performance logging)
    """
    import subprocess

    sa = f"engine-b-sa@{PROJECT_ID}.iam.gserviceaccount.com"

    roles = [
        "roles/aiplatform.user",
        "roles/bigquery.dataEditor",
        "roles/pubsub.publisher",
        "roles/logging.logWriter",
    ]

    for role in roles:
        cmd = [
            "gcloud", "projects", "add-iam-policy-binding", PROJECT_ID,
            "--member", f"serviceAccount:{sa}",
            "--role", role,
            "--quiet",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"✅ IAM: {sa} → {role}")
            else:
                logger.warning(f"IAM grant failed: {result.stderr.strip()}")
        except Exception as e:
            logger.warning(f"IAM command failed: {e}")

    # GCS bucket-level grant
    gcs_cmd = [
        "gcloud", "storage", "buckets", "add-iam-policy-binding",
        f"gs://infinity-ai-models-vault",
        "--member", f"serviceAccount:{sa}",
        "--role", "roles/storage.objectAdmin",
        "--project", PROJECT_ID,
    ]
    try:
        result = subprocess.run(gcs_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info(f"✅ GCS IAM: {sa} → roles/storage.objectAdmin on infinity-ai-models-vault")
    except Exception as e:
        logger.warning(f"GCS IAM failed: {e}")


def create_bq_tables() -> None:
    """Create required BigQuery tables for model performance and feature baseline."""
    from google.cloud import bigquery

    client  = bigquery.Client(project=PROJECT_ID)
    dataset = "market_data"

    tables = {
        "model_performance": """
            symbol STRING NOT NULL,
            model_name STRING NOT NULL,
            accuracy FLOAT64,
            f1_score FLOAT64,
            log_loss FLOAT64,
            trained_at STRING NOT NULL,
            version STRING
        """,
        "feature_baselines": """
            symbol STRING NOT NULL,
            feature_name STRING NOT NULL,
            mean FLOAT64,
            std FLOAT64,
            p5 FLOAT64,
            p25 FLOAT64,
            p50 FLOAT64,
            p75 FLOAT64,
            p95 FLOAT64,
            created_at STRING NOT NULL
        """,
        "feature_store": """
            symbol STRING NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            split STRING,
            target INT64
        """,
    }

    for table_name, schema_sql in tables.items():
        table_id  = f"{PROJECT_ID}.{dataset}.{table_name}"
        schema    = []
        for field_def in [l.strip() for l in schema_sql.strip().split(",") if l.strip()]:
            parts = field_def.split()
            if len(parts) >= 2:
                mode  = "REQUIRED" if "NOT NULL" in field_def else "NULLABLE"
                bq_type_map = {
                    "STRING": "STRING", "FLOAT64": "FLOAT64",
                    "INT64": "INT64", "TIMESTAMP": "TIMESTAMP",
                }
                field_type = bq_type_map.get(parts[1], "STRING")
                schema.append(bigquery.SchemaField(parts[0], field_type, mode=mode))

        table = bigquery.Table(table_id, schema=schema) if schema else None
        if table:
            try:
                client.create_table(table, exists_ok=True)
                logger.info(f"✅ BQ table ready: {table_id}")
            except Exception as e:
                logger.warning(f"BQ table create failed {table_id}: {e}")


def print_summary() -> None:
    """Print setup summary."""
    print("\n" + "═" * 60)
    print("  🚀 INFINITYAI.PRO — NIGHTLY RETRAIN PIPELINE SETUP")
    print("═" * 60)
    print(f"  Project:    {PROJECT_ID}")
    print(f"  Region:     {REGION}")
    print(f"  Schedule:   Mon-Fri 18:00 IST (12:30 UTC)")
    print(f"  Symbols:    {', '.join(SYMBOLS)}")
    print(f"  Engine B:   {ENGINE_B_URL}")
    print(f"  Model Vault: gs://infinity-ai-models-vault/")
    print("  Cost:       ~₹120/run × 5 symbols = ~₹600/night")
    print()
    print("  Pub/Sub topics:")
    print(f"    • {PUBSUB_TOPIC}")
    print(f"    • {PUBSUB_DRIFT}")
    print()
    print("  Cloud Scheduler jobs:")
    for i, sym in enumerate(SYMBOLS):
        print(f"    • infinity-retrain-{sym.lower()} @ 18:{i*10:02d} IST Mon-Fri")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InfinityAI.Pro — Nightly Retrain Pipeline Setup")
    parser.add_argument("--project",    type=str, default=PROJECT_ID)
    parser.add_argument("--engine-b",   type=str, default=ENGINE_B_URL)
    parser.add_argument("--skip-iam",   action="store_true", help="Skip IAM setup")
    parser.add_argument("--skip-bq",    action="store_true", help="Skip BQ table creation")
    parser.add_argument("--skip-sched", action="store_true", help="Skip scheduler creation")
    args = parser.parse_args()

    PROJECT_ID   = args.project
    ENGINE_B_URL = args.engine_b

    print_summary()

    logger.info("📋 Step 1: Creating Pub/Sub topics...")
    create_pubsub_topics()

    if not args.skip_iam:
        logger.info("🔐 Step 2: Setting up IAM permissions...")
        setup_vertex_service_account()

    if not args.skip_bq:
        logger.info("📊 Step 3: Creating BigQuery tables...")
        create_bq_tables()

    if not args.skip_sched:
        logger.info("⏰ Step 4: Creating Cloud Scheduler jobs...")
        create_cloud_scheduler_jobs()

    logger.info("✅ Nightly Retraining Pipeline Setup COMPLETE!")
    logger.info("   Retraining will begin tonight at 18:00 IST.")
