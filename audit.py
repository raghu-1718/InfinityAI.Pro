import json
import subprocess
from google.cloud import storage, bigquery

print('--- Phase 1: Engine Configs ---')
for svc in ['engine-a', 'engine-b', 'engine-c']:
    try:
        with open(f'{svc}.json') as f:
            d = json.load(f)
            template = d.get('spec', {}).get('template', {})
            containers = template.get('spec', {}).get('containers', [{}])[0]
            min_inst = template.get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/minScale', '0')
            max_inst = template.get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/maxScale', '100')
            vpc_egress = template.get('metadata', {}).get('annotations', {}).get('run.googleapis.com/vpc-access-egress', 'none')
            limits = containers.get('resources', {}).get('limits', {})
            print(f'[{svc}] min={min_inst} max={max_inst} limits={limits} egress={vpc_egress}')
    except Exception as e:
        print(f'Error reading {svc}: {e}')

print('\n--- Phase 3: BigQuery & GCS ---')
bq = bigquery.Client()
q = bq.query('SELECT max(timestamp) as last_update, count(*) as total_rows FROM `project-841b7f97-5ee3-4fbe-920.infinity_dataset.market_ticks_history`')
res = list(q.result())[0]
print(f'BQ Table: total={res.total_rows}, last_update={res.last_update}')

st = storage.Client()
bucket = st.bucket('infinity-ai-models-vault')
for blob in bucket.list_blobs():
    print(f'GCS Blob: {blob.name}, updated={blob.updated}, size={blob.size}')
