import sys
import os
from google.cloud import bigquery

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

project_id = 'project-841b7f97-5ee3-4fbe-920'
client = bigquery.Client(project=project_id)

print('=== BIGQUERY REAL-TIME STREAMING TICKS QUERY ===')
query = f'SELECT data, message_id, publish_time FROM `{project_id}.market_data.live_ticks` ORDER BY publish_time DESC LIMIT 5'
query_job = client.query(query)
rows = list(query_job.result())

print(f'✅ BigQuery Live Stream Rows Found: {len(rows)}')
for r in rows:
    print(f'   - [MsgID: {r.message_id}] | Time: {r.publish_time}')
    print(f'     Data: {r.data}')
