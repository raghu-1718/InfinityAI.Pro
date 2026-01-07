#!/usr/bin/env python3
"""
Compare live NIFTY price from Dhan with Firestore 'market_data' (if present).

Usage:
  # Option A: provide DHAN_ACCESS_TOKEN in env
  export DHAN_ACCESS_TOKEN=...
  python compare_nifty.py

  # Option B: if using Secret Manager, set USE_SECRET_MANAGER=true and ensure GOOGLE_APPLICATION_CREDENTIALS is set
"""
import os
import requests
from google.cloud import firestore
from google.cloud import secretmanager

PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GCLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
USE_SECRET_MANAGER = os.getenv("USE_SECRET_MANAGER") == "true"

def get_dhan_token():
    token = os.getenv("DHAN_ACCESS_TOKEN")
    if token:
        return token
    if USE_SECRET_MANAGER and PROJECT_ID:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/dhan_service_access_token/versions/latest"
        try:
            version = client.access_secret_version(request={"name": name})
            return version.payload.data.decode("utf8")
        except Exception as e:
            print("Secret Manager token read failed:", e)
    # Gracefully skip when no token available (CI/build environments)
    return None

def fetch_nifty_from_dhan(token: str):
    url = "https://api.dhan.co/market/nse/indices/NIFTY/quote"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_nifty_from_firestore():
    db = firestore.Client()
    try:
        doc = db.collection("market_data").document("NIFTY").get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print("Could not read market_data/NIFTY from Firestore:", e)
        return None

def main():
    token = get_dhan_token()
    if not token:
        print("Skipping live NIFTY comparison: no DHAN token available.")
        return
    print("Fetching live NIFTY from Dhan...")
    nifty = fetch_nifty_from_dhan(token)
    print("Dhan response:", nifty)

    firestore_nifty = fetch_nifty_from_firestore()
    print("Firestore NIFTY:", firestore_nifty)

    # Basic comparison
    try:
        live_price = float(nifty.get("last_price") or nifty.get("last") or nifty.get("price") or 0)
    except Exception:
        live_price = None

    if firestore_nifty and live_price:
        fs_price = float(firestore_nifty.get("price") or firestore_nifty.get("last_price") or 0)
        diff = live_price - fs_price
        print(f"Price diff: {diff} (live {live_price} vs firestore {fs_price})")
    else:
        print("Insufficient data for numeric comparison.")

if __name__ == '__main__':
    main()
