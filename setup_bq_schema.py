from google.cloud import bigquery

project_id = "project-841b7f97-5ee3-4fbe-920"
location = "asia-south1"

client = bigquery.Client(project=project_id, location=location)

# 1. Create Dataset if it doesn't exist
dataset_id = f"{project_id}.market_data"
dataset = bigquery.Dataset(dataset_id)
dataset.location = location
try:
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"✅ Dataset {dataset.dataset_id} created or already exists in {location}.")
except Exception as e:
    print(f"❌ Error creating dataset: {e}")

# 2. Create options_ticks Table with Partitioning and Clustering
table_id = f"{dataset_id}.options_ticks"
schema = [
    bigquery.SchemaField("trade_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("underlying", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("strike_price", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("option_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("expiry_date", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("premium_price", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("volume", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("open_interest", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("implied_volatility", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
]

table = bigquery.Table(table_id, schema=schema)
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="timestamp",
)
table.clustering_fields = ["underlying", "option_type"]

try:
    table = client.create_table(table, exists_ok=True)
    print(f"✅ Table {table.table_id} created successfully with partitioning and clustering.")
except Exception as e:
    print(f"❌ Error creating table: {e}")
