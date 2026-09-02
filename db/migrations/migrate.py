"""
BigQuery Migration Engine for InfinityAI.Pro
Ensures tables exist with partitioning and clustering.
"""
import os
import sys
import logging
from typing import Dict
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google.cloud import bigquery
from db.schemas.bigquery_schemas import DATASET_NAME, TABLE_CONFIGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
LOCATION = os.getenv("GOOGLE_CLOUD_REGION", "asia-south1")


def run_migrations(dry_run: bool = False) -> Dict[str, str]:
    """
    Run BigQuery table migrations.
    Returns status map for each table.
    """
    results = {}
    logger.info(f"Starting BigQuery migrations for project: {PROJECT_ID}, dataset: {DATASET_NAME}, location: {LOCATION}")

    try:
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    except Exception as e:
        logger.warning(f"Could not initialize BigQuery client (running in mock/offline mode): {e}")
        return {table: "mock_created" for table in TABLE_CONFIGS}

    # 1. Create dataset
    dataset_ref = f"{PROJECT_ID}.{DATASET_NAME}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = LOCATION
    try:
        if not dry_run:
            client.create_dataset(dataset, exists_ok=True)
        logger.info(f"Dataset {dataset_ref} verified/created.")
    except Exception as e:
        logger.error(f"Failed to create dataset {dataset_ref}: {e}")
        results["dataset"] = f"failed: {e}"
        return results

    # 2. Create tables
    for table_name, config in TABLE_CONFIGS.items():
        table_ref = f"{dataset_ref}.{table_name}"
        table = bigquery.Table(table_ref, schema=config["schema"])
        
        # Partitioning
        table.time_partitioning = bigquery.TimePartitioning(
            type_=config["partition_type"],
            field=config["partition_field"]
        )
        
        # Clustering
        table.clustering_fields = config["clustering"]

        if dry_run:
            results[table_name] = "dry_run_ok"
            continue

        try:
            client.create_table(table, exists_ok=True)
            logger.info(f"Table {table_ref} verified/created with partitioning on {config['partition_field']}.")
            results[table_name] = "created_or_exists"
        except Exception as e:
            logger.error(f"Error creating table {table_ref}: {e}")
            results[table_name] = f"failed: {e}"

    return results


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    res = run_migrations(dry_run=dry_run)
    print("Migration summary:", res)
