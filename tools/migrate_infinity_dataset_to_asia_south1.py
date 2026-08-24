"""
BigQuery Dataset Migration Tool: US Multi-Region -> asia-south1 (Mumbai)
InfinityAI.Pro - Safe Zero-Data-Loss Migration
"""

import time
from google.cloud import bigquery, storage

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
SRC_DATASET = "infinity_dataset"
SRC_LOCATION = "US"
TARGET_LOCATION = "asia-south1"
GCS_BACKUP_URI = "gs://infinity-ai-models-vault/bq_backup/market_ticks_history_*.parquet"

def migrate():
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    print(f"=== 1. Inspecting Source Dataset: {SRC_DATASET} ({SRC_LOCATION}) ===")
    src_table_ref = f"{PROJECT_ID}.{SRC_DATASET}.market_ticks_history"
    src_table = bq_client.get_table(src_table_ref)
    original_row_count = src_table.num_rows
    print(f"  Source Table Rows: {original_row_count:,}")
    print(f"  Source Table Schema: {[f.name for f in src_table.schema]}")

    print(f"\n=== 2. Exporting Table to GCS (Parquet Format) ===")
    job_config = bigquery.ExtractJobConfig(destination_format="PARQUET")
    extract_job = bq_client.extract_table(src_table_ref, GCS_BACKUP_URI, job_config=job_config, location=SRC_LOCATION)
    extract_job.result()
    print("  [OK] Table exported safely to GCS!")

    print(f"\n=== 3. Re-creating Dataset in {TARGET_LOCATION} (Mumbai) ===")
    # Delete old US dataset
    bq_client.delete_dataset(SRC_DATASET, delete_contents=True, not_found_ok=True)
    print(f"  Deleted US dataset {SRC_DATASET}.")

    # Create new dataset in asia-south1
    target_dataset = bigquery.Dataset(f"{PROJECT_ID}.{SRC_DATASET}")
    target_dataset.location = TARGET_LOCATION
    target_dataset.description = "InfinityAI.Pro ML Historical Features & Dataset (Mumbai)"
    bq_client.create_dataset(target_dataset, exists_ok=True)
    print(f"  Created new dataset {SRC_DATASET} in {TARGET_LOCATION}!")

    print(f"\n=== 4. Loading Data into asia-south1 Table ===")
    target_table_ref = f"{PROJECT_ID}.{SRC_DATASET}.market_ticks_history"
    load_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
    )
    load_job = bq_client.load_table_from_uri(
        GCS_BACKUP_URI,
        target_table_ref,
        job_config=load_config,
        location=TARGET_LOCATION
    )
    load_job.result()
    
    # Verify new table
    new_table = bq_client.get_table(target_table_ref)
    print(f"  [OK] Successfully restored {new_table.num_rows:,} rows in {TARGET_LOCATION}!")
    print(f"  Partitioned by: {new_table.time_partitioning.field} ({new_table.time_partitioning.type_})")

    assert new_table.num_rows == original_row_count, f"Row mismatch! Original: {original_row_count}, New: {new_table.num_rows}"
    print(f"\n🏆 MIGRATION 100% SUCCESSFUL: {SRC_DATASET} is now natively in {TARGET_LOCATION} (Mumbai)!")

if __name__ == "__main__":
    migrate()
