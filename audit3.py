import time
import requests
import json
from google.cloud import bigquery

print("=== Phase 1: Health Latencies ===")
urls = {
    'Engine-A': 'https://engine-a-313407263327.asia-south1.run.app/api/health',
    'Engine-B': 'https://engine-b-313407263327.asia-south1.run.app/api/health',
    'Engine-C': 'https://engine-c-313407263327.asia-south1.run.app/api/health'
}
for name, url in urls.items():
    try:
        t0 = time.time()
        res = requests.get(url, timeout=5)
        latency = (time.time() - t0) * 1000
        print(f"{name}: {res.status_code} | Latency: {latency:.2f} ms")
    except Exception as e:
        print(f"{name}: Error - {e}")

print("\n=== Phase 4: BigQuery ML Predict ===")
try:
    bq = bigquery.Client()
    q = """
    SELECT * FROM ML.PREDICT(
      MODEL `project-841b7f97-5ee3-4fbe-920.infinity_dataset.xgboost_live_model`,
      (SELECT 55.0 as rsi_14, 1 as macd_crossover, 0.5 as vwap_distance, 15.0 as atr_volatility)
    )
    """
    job = bq.query(q)
    results = list(job.result())
    for row in results:
        print(f"Prediction: {row.get('predicted_signal_outcome', 'N/A')}")
        print(f"Probabilities: {row.get('predicted_signal_outcome_probs', 'N/A')}")
except Exception as e:
    print(f"BQML Predict Error: {e}")
