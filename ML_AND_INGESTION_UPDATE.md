InfinityAI.Pro ML & Data Ingestion Optimization Plan

This document outlines the precise code modifications and architectural considerations to optimize our ML pipeline (Engine-B) and data ingestion (Engine-C) components. The focus is on leveraging the `dhan_client_wrapper` for robust API interaction, enhancing BigQuery ingestion efficiency, and integrating options-derived features (PCR, OI) into the ML model training.

---

## 1. Engine-C: `backend/engine-c/src/options_chain_ingestor.py` Optimization

**Objective:** Enhance robustness against API rate limits, improve error handling for malformed data, and ensure efficient BigQuery streaming.

**Analysis:**
*   The `options_chain_ingestor.py` currently uses `requests.post` directly for DhanHQ API calls (`expirylist` and `optionchain`). This bypasses the `DhanClient` wrapper's caching and rate-limit handling implemented in `dhan_client_wrapper.py`.
*   The `dhanhq` library (wrapped by `DhanClient`) has an `option_chain` method, but not a direct `expirylist` method. We will integrate `dhan_client.option_chain` and keep `requests.post` for `expirylist` but make it more robust.
*   BigQuery insertion uses `insert_rows_json` with batching, which is good. Error handling can be slightly improved with more specific logging.
*   Malformed tick handling can be made more explicit using `.get()` with default values.

**Proposed Changes:**

**A. Integrate `DhanClient` for `option_chain` calls and enhance `expirylist` robustness.**
**B. Improve error handling for malformed option tick data.**
**C. Refine BigQuery insertion logging.**

---

### `backend/engine-c/src/options_chain_ingestor.py` - Rewritten Code Block

```python
import os
import time
import asyncio
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from google.cloud import bigquery

# Import the custom DhanClient wrapper
from .user_credentials import UserCredentialsManager
from .dhan_client_wrapper import create_dhan_client, DhanEnvironment

logger = logging.getLogger("options_chain_ingestor")
logger.setLevel(logging.INFO) # Ensure logging level is set

# Core Indian Index Underlyings for Options Ingestion
SUPPORTED_OPTIONS_INDICES = [
    {"symbol": "NIFTY", "sec_id": 13, "segment": "IDX_I"},
    {"symbol": "BANKNIFTY", "sec_id": 25, "segment": "IDX_I"},
    {"symbol": "SENSEX", "sec_id": 51, "segment": "IDX_I"},
    {"symbol": "FINNIFTY", "sec_id": 27, "segment": "IDX_I"},
    {"symbol": "MIDCPNIFTY", "sec_id": 442, "segment": "IDX_I"},
]

class OptionsChainIngestor:
    def __init__(self, project_id: str = "project-841b7f97-5ee3-4fbe-920"):
        self.project_id = project_id
        # Ensure the dataset 'market_data' exists and is in 'asia-south1'
        self.table_id = f"{project_id}.market_data.options_ticks"
        self.credentials_manager = UserCredentialsManager()
        self._bq_client = None

    @property
    def bq_client(self):
        if self._bq_client is None:
            try:
                # Initialize BigQuery client with explicit project
                self._bq_client = bigquery.Client(project=self.project_id)
                logger.info(f"BigQuery client initialized for project: {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize BigQuery client: {e}")
                self._bq_client = None
        return self._bq_client

    async def ingest_live_option_chains(self, user_id: str = "raghu_primary") -> Dict[str, Any]:
        """
        Polls DhanHQ v2 Option Chain API for all supported indices and inserts ticks into BigQuery.
        Leverages DhanClient wrapper for rate-limit handling where possible.
        """
        t0 = time.time()
        creds = await self.credentials_manager.get_user_credentials(user_id)
        client_id = creds.get("client_id") or creds.get("dhan_client_id")
        access_token = creds.get("access_token") or creds.get("dhan_access_token")

        if not access_token or not client_id:
            logger.error("❌ Dhan credentials unavailable in Firestore Vault for options ingestion")
            return {"status": "error", "message": "Dhan credentials not found"}

        # Initialize DhanClient wrapper for SDK calls
        # Note: DhanClient wraps dhanhq SDK, which may not have direct methods for all v2 API endpoints.
        # For endpoints not in SDK (like expirylist), we'll use requests directly with enhanced error handling.
        dhan_client_wrapper = create_dhan_client(client_id, access_token, environment=DhanEnvironment.PRODUCTION)

        # Headers for direct HTTP requests (e.g., expirylist)
        http_headers = {
            "access-token": access_token,
            "client-id": client_id,
            "Content-Type": "application/json"
        }

        rows_to_insert: List[Dict[str, Any]] = []
        indices_summary = {}

        for idx in SUPPORTED_OPTIONS_INDICES:
            symbol = idx["symbol"]
            sec_id = idx["sec_id"]
            segment = idx["segment"]

            # 1. Resolve nearest active expiry (using direct HTTP call as dhanhq SDK lacks this)
            exp_url = "https://api.dhan.co/v2/optionchain/expirylist"
            exp_payload = {"UnderlyingScrip": sec_id, "UnderlyingSeg": segment}
            target_expiry = None

            try:
                # Use httpx for more robust HTTP requests, if available, otherwise requests
                # For simplicity, sticking with requests as it's already imported
                exp_resp = requests.post(exp_url, headers=http_headers, json=exp_payload, timeout=8)
                exp_resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                exp_list = exp_resp.json().get("data", []) or []
                if exp_list:
                    target_expiry = exp_list[0]
                else:
                    logger.warning(f"No expiry dates found for {symbol} from DhanHQ.")
            except requests.exceptions.Timeout:
                logger.error(f"Timeout fetching expiry for {symbol} from DhanHQ.")
            except requests.exceptions.RequestException as e:
                logger.error(f"HTTP error fetching expiry for {symbol}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching expiry for {symbol}: {e}")

            if not target_expiry:
                logger.warning(f"Skipping {symbol}: Could not determine target expiry.")
                continue

            # 2. Fetch full option chain depth using DhanClient wrapper
            # The dhanhq SDK's option_chain method is wrapped by DhanClient
            try:
                oc_data = dhan_client_wrapper.option_chain(
                    security_id=sec_id,
                    exchange_segment=segment,
                    expiry_date=target_expiry
                )

                if oc_data and oc_data.get("status") == "success":
                    oc_dict = oc_data.get("data", {}).get("oc", {}) or {}
                    symbol_rows = 0

                    for strike_str, strike_info in oc_dict.items():
                        try:
                            strike_price = int(float(strike_str))
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping malformed strike price '{strike_str}' for {symbol}.")
                            continue

                        current_timestamp = datetime.now(timezone.utc).isoformat()

                        # Call Option (CE)
                        ce = strike_info.get("ce")
                        if ce and isinstance(ce, dict):
                            ce_ltp = float(ce.get("last_price") or ce.get("ltp") or 0.0)
                            if ce_ltp > 0: # Only ingest if LTP is meaningful
                                rows_to_insert.append({
                                    "trade_id": f"{symbol}_{strike_price}_CE_{int(time.time()*1000)}", # Unique ID
                                    "underlying": symbol,
                                    "strike_price": strike_price,
                                    "option_type": "CE",
                                    "expiry_date": target_expiry,
                                    "premium_price": ce_ltp,
                                    "volume": int(ce.get("volume") or ce.get("vol") or 0),
                                    "open_interest": int(ce.get("oi") or ce.get("open_interest") or 0),
                                    "implied_volatility": float(ce.get("iv") or 0.0),
                                    "timestamp": current_timestamp
                                })
                                symbol_rows += 1

                        # Put Option (PE)
                        pe = strike_info.get("pe")
                        if pe and isinstance(pe, dict):
                            pe_ltp = float(pe.get("last_price") or pe.get("ltp") or 0.0)
                            if pe_ltp > 0: # Only ingest if LTP is meaningful
                                rows_to_insert.append({
                                    "trade_id": f"{symbol}_{strike_price}_PE_{int(time.time()*1000)}", # Unique ID
                                    "underlying": symbol,
                                    "strike_price": strike_price,
                                    "option_type": "PE",
                                    "expiry_date": target_expiry,
                                    "premium_price": pe_ltp,
                                    "volume": int(pe.get("volume") or pe.get("vol") or 0),
                                    "open_interest": int(pe.get("oi") or pe.get("open_interest") or 0),
                                    "implied_volatility": float(pe.get("iv") or 0.0),
                                    "timestamp": current_timestamp
                                })
                                symbol_rows += 1

                    indices_summary[symbol] = {
                        "expiry": target_expiry,
                        "contracts_extracted": symbol_rows
                    }
                    logger.info(f"Extracted {symbol_rows} option contracts for {symbol} (Expiry: {target_expiry}).")
                elif oc_data and oc_data.get("status") == "upstream_maintenance":
                    logger.warning(f"DhanHQ upstream maintenance for {symbol} option chain. Skipping this cycle.")
                else:
                    logger.error(f"Failed to fetch option chain for {symbol}: {oc_data.get('remarks', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Error fetching option chain for {symbol} using DhanClient: {e}")

        # 3. Stream in batches into BigQuery options_ticks
        total_inserted = 0
        batch_size = 500 # Optimal batch size for streaming inserts
        if not self.bq_client:
            logger.critical("BigQuery client not initialized. Cannot insert rows.")
            return {"status": "error", "message": "BigQuery client not available"}

        if not rows_to_insert:
            logger.info("No option contracts to insert into BigQuery.")
            return {
                "status": "success",
                "total_inserted": 0,
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "indices": indices_summary,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i + batch_size]
            try:
                errors = self.bq_client.insert_rows_json(self.table_id, batch)
                if not errors:
                    total_inserted += len(batch)
                    logger.debug(f"Successfully inserted {len(batch)} rows into BigQuery.")
                else:
                    logger.error(f"BigQuery streaming errors for batch starting at index {i}: {errors[:5]}") # Log first 5 errors
            except Exception as e:
                logger.error(f"Unexpected error during BigQuery batch insert at index {i}: {e}")

        duration_ms = round((time.time() - t0) * 1000, 2)
        logger.info(f"✅ Options Ingestion: Streamed {total_inserted} contracts into {self.table_id} in {duration_ms}ms")

        return {
            "status": "success",
            "total_inserted": total_inserted,
            "latency_ms": duration_ms,
            "indices": indices_summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

options_ingestor = OptionsChainIngestor()

```

**Execution Instructions for Engine-C:**
1.  Ensure `dhan_client_wrapper.py` is in the same `src` directory.
2.  Verify the `GOOGLE_CLOUD_PROJECT` environment variable is correctly set for the Cloud Run service.
3.  Confirm the BigQuery dataset `market_data` and table `options_ticks` exist in the `asia-south1` region with the appropriate schema:
    ```sql
    CREATE TABLE `your-project-id.market_data.options_ticks` (
        trade_id STRING NOT NULL,
        underlying STRING NOT NULL,
        strike_price INTEGER NOT NULL,
        option_type STRING NOT NULL,
        expiry_date STRING NOT NULL,
        premium_price FLOAT64 NOT NULL,
        volume INTEGER NOT NULL,
        open_interest INTEGER NOT NULL,
        implied_volatility FLOAT64 NOT NULL,
        timestamp TIMESTAMP NOT NULL
    )
    PARTITION BY DATE(timestamp)
    CLUSTER BY underlying, option_type;
    ```
4.  Deploy the updated `options_chain_ingestor.py` to Cloud Run.

---

## 2. Engine-B: `backend/engine-b/src/training/train_tri_model.py` Optimization

**Objective:** Integrate options-derived features (PCR, OI) from BigQuery into the ML model training, and refine the data pipeline for efficiency on a dedicated VM.

**Analysis:**
*   The current `train_tri_model.py` fetches only OHLCV data (from Engine-C/Yahoo) and calculates technical indicators. It completely lacks options data.
*   To incorporate PCR and OI, we need to:
    1.  Query the `market_data.options_ticks` table in BigQuery.
    2.  Aggregate this data to derive daily PCR, total CE OI, and total PE OI for each index.
    3.  Merge these options features with the existing OHLCV data.
    4.  Add these new features to the `feature_cols` list for model training.
*   For a dedicated VM, local caching of the pre-processed DataFrame can significantly speed up iterative development or re-runs if the underlying data hasn't changed.

**Proposed Changes:**

**A. Add BigQuery client and a new function `fetch_options_features_from_bigquery`.**
**B. Modify `calculate_features` to accept and merge options data, then compute PCR and OI-related features.**
**C. Update `train_tri_model_ensemble` to orchestrate fetching both OHLCV and options data, and to use local caching.**

---

### `backend/engine-b/src/training/train_tri_model.py` - Rewritten Code Block

```python
"""
InfinityAI.Pro — Institutional Tri-Model MLOps Training Pipeline
Pure Index F&O Engine: Trains CatBoost, LightGBM, XGBoost, and RandomForest on Real Indian Index Data.
Supports: NIFTY, BANKNIFTY, SENSEX, FINNIFTY, MIDCPNIFTY.
Saves and publishes trained model weights to gs://infinity-ai-models-vault/.
"""

import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

# Ensure path includes engine-b src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ML Frameworks
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    from google.cloud import storage, bigquery
    HAS_GCS = True
    HAS_BIGQUERY = True
except ImportError:
    HAS_GCS = False
    HAS_BIGQUERY = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InfinityAI.TriModelTrainer")

# Pure Indian Index Master Mapping for DhanHQ API v2
INDEX_MASTER_MAP = {
    "NIFTY": ("13", "IDX_I"),
    "NIFTY50": ("13", "IDX_I"),
    "BANKNIFTY": ("25", "IDX_I"),
    "SENSEX": ("51", "IDX_I"),
    "BSESN": ("51", "IDX_I"),
    "FINNIFTY": ("27", "IDX_I"),
    "MIDCPNIFTY": ("442", "IDX_I")
}

# BigQuery Project ID (replace with your actual project ID or use env var)
BIGQUERY_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")


def calculate_features(df_ohlcv: pd.DataFrame, df_options: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, list]:
    """
    Engineer institutional technical features on Index OHLCV dataset,
    and integrate options-derived features like PCR and Open Interest.
    """
    data = df_ohlcv.copy()
    
    # Ensure 'date' column for merging
    if 'date' not in data.columns:
        if 'Date' in data.columns:
            data['date'] = pd.to_datetime(data['Date']).dt.date
        elif data.index.name == 'Date':
            data['date'] = pd.to_datetime(data.index).dt.date
        else:
            # Attempt to infer date from index if not named 'Date'
            try:
                data['date'] = pd.to_datetime(data.index).dt.date
            except Exception:
                logger.warning("Could not infer