import os
import json
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from google.cloud import pubsub_v1

app = FastAPI(title="news-ingestion")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
TOPIC_NAME = os.getenv("PUBSUB_TOPIC_NEWS_RAW", "news.raw")

if not PROJECT_ID:
    raise RuntimeError("GOOGLE_CLOUD_PROJECT is required")

publisher = pubsub_v1.PublisherClient()
TOPIC_PATH = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "news-ingestion",
        "project": PROJECT_ID,
        "topic": TOPIC_NAME,
    }

@app.post("/ingest/news")
async def ingest_news(payload: Dict[str, Any]) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = payload.get("records", [])
    if not isinstance(records, list) or not records:
        raise HTTPException(status_code=400, detail="records must be a non-empty list")

    published = 0
    for record in records:
        data = json.dumps(record).encode("utf-8")
        future = publisher.publish(TOPIC_PATH, data)
        future.result()
        published += 1

    return {"status": "ok", "published": published}
