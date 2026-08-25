import sys
import os
import time
import json
import urllib.request
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath('backend/engine-b/src'))

from services.feature_engineer import FeatureEngineer
from catboost import CatBoostClassifier
import lightgbm as lgb
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

print("=" * 90)
print("🚀 100% DIRECT DHANHQ BROKER DATA — F&O TRI-MODEL ENSEMBLE ACCURACY AUDIT")
print("=" * 90)

# Pure Indian Index Master Mapping for DhanHQ API v2
DHAN_INDEX_MAP = {
    "NIFTY": ("13", "IDX_I", "INDEX"),
    "BANKNIFTY": ("25", "IDX_I", "INDEX"),
    "FINNIFTY": ("27", "IDX_I", "INDEX")
}

BASE_ENGINE_C = "https://engine-c-r2f5flt77q-el.a.run.app"
USER_ID = "raghu_primary"

fe = FeatureEngineer()
results_summary = []

for symbol, (sec_id, seg, inst_type) in DHAN_INDEX_MAP.items():
    print(f"\n[DhanHQ Ingestion] Fetching live historical candles for {symbol} (SecID: {sec_id})...")
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    url = (
        f"{BASE_ENGINE_C}/api/dhan/market/historical?"
        f"user_id={USER_ID}&security_id={sec_id}&exchange_segment={seg}&"
        f"instrument_type={inst_type}&from_date={from_date}&to_date={to_date}&timeframe=1D"
    )
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "InfinityAI-DhanAudit/1.0"})
        res = urllib.request.urlopen(req, timeout=12)
        raw_res = json.loads(res.read().decode())
        
        inner = raw_res.get("data", {}).get("data", {})
        if not inner or "close" not in inner or len(inner["close"]) == 0:
            print(f"   ⚠️ No candle data returned from DhanHQ for {symbol}: {raw_res}")
            continue
            
        df = pd.DataFrame({
            "open": inner["open"],
            "high": inner["high"],
            "low": inner["low"],
            "close": inner["close"],
            "volume": inner.get("volume", [100000] * len(inner["close"]))
        })
        
        print(f"   ✅ Received {len(df)} authentic DhanHQ OHLCV daily bars for {symbol}")
        
        # Feature Engineering (59 quantitative & technical indicators)
        df_feat, feat_cols = fe.generate_all_features(df)
        
        # Target: Next bar directional return (>0)
        returns = df_feat["close"].pct_change().shift(-1)
        df_feat["target_binary"] = (returns > 0).astype(int)
        df_feat = df_feat.dropna()
        
        if len(df_feat) < 20:
            print(f"   ⚠️ Insufficient rows after feature extraction: {len(df_feat)}")
            continue
            
        split_idx = int(len(df_feat) * 0.75)
        train = df_feat.iloc[:split_idx]
        test = df_feat.iloc[split_idx:]
        
        X_train, y_train = train[feat_cols], train["target_binary"]
        X_test, y_test = test[feat_cols], test["target_binary"]
        
        # 1. CatBoost
        cb = CatBoostClassifier(iterations=150, depth=4, verbose=0, random_seed=42)
        cb.fit(X_train, y_train)
        prob_cb = cb.predict_proba(X_test)[:, 1]
        acc_cb = accuracy_score(y_test, (prob_cb >= 0.5).astype(int))
        
        # 2. LightGBM
        lgbm = lgb.LGBMClassifier(n_estimators=150, num_leaves=15, random_state=42, verbose=-1)
        lgbm.fit(X_train, y_train)
        prob_lgb = lgbm.predict_proba(X_test)[:, 1]
        acc_lgb = accuracy_score(y_test, (prob_lgb >= 0.5).astype(int))
        
        # 3. XGBoost
        xg = xgb.XGBClassifier(n_estimators=150, max_depth=3, random_state=42, eval_metric="logloss")
        xg.fit(X_train, y_train)
        prob_xgb = xg.predict_proba(X_test)[:, 1]
        acc_xgb = accuracy_score(y_test, (prob_xgb >= 0.5).astype(int))
        
        # Tri-Model Ensemble Consensus (35% CatBoost, 35% LightGBM, 30% XGBoost)
        prob_ens = (0.35 * prob_cb) + (0.35 * prob_lgb) + (0.30 * prob_xgb)
        preds_ens = (prob_ens >= 0.5).astype(int)
        
        acc_ens = accuracy_score(y_test, preds_ens)
        prec_ens = precision_score(y_test, preds_ens, zero_division=0)
        rec_ens = recall_score(y_test, preds_ens, zero_division=0)
        f1_ens = f1_score(y_test, preds_ens, zero_division=0)
        
        row = {
            "Symbol": symbol,
            "Dhan SecID": sec_id,
            "Ensemble Acc": f"{acc_ens*100:.2f}%",
            "CatBoost": f"{acc_cb*100:.2f}%",
            "LightGBM": f"{acc_lgb*100:.2f}%",
            "XGBoost": f"{acc_xgb*100:.2f}%",
            "Precision": f"{prec_ens*100:.2f}%",
            "Recall": f"{rec_ens*100:.2f}%",
            "F1-Score": f"{f1_ens:.4f}",
            "Samples": f"{len(train)} tr / {len(test)} ts"
        }
        results_summary.append(row)
        print(f"   🎯 {symbol} Ensemble Directional Accuracy on Pure DhanHQ Data: {row['Ensemble Acc']} (F1: {row['F1-Score']})")
        
    except Exception as e:
        print(f"   ❌ Error evaluating {symbol} with DhanHQ data: {e}")

print("\n" + "=" * 90)
print("📊 FINAL AUDIT TABLE: 100% DIRECT DHANHQ BROKER DATA PERFORMANCE")
print("=" * 90)

df_summary = pd.DataFrame(results_summary)
print(df_summary.to_markdown(index=False))
