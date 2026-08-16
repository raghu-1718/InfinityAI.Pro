from google.cloud import bigquery

project_id = "project-841b7f97-5ee3-4fbe-920"
location = "asia-south1"

# Explicitly set client location
client = bigquery.Client(project=project_id, location=location)

query = f"SELECT underlying, COUNT(*) as cnt FROM `{project_id}.market_data.options_ticks` GROUP BY underlying"

try:
    # Pass location job config explicitly
    job_config = bigquery.QueryJobConfig()
    query_job = client.query(query, job_config=job_config, location=location)
    results = [dict(r) for r in query_job.result()]
    print("✅ BigQuery Options Ticks Check Successful (Table Exists and is Queryable):")
    print(results)
except Exception as e:
    print(f"❌ BigQuery Query Error: {e}")
