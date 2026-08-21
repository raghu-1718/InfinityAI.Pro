import sys
import os
import time
import json
import numpy as np
import pandas as pd

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath('backend/engine-b/src'))

from training.train_ensemble import train_full_ensemble

symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]

print("=" * 80)
print("🚀 REAL-TIME F&O INSTRUMENTS ENSEMBLE ACCURACY & PERFORMANCE AUDIT")
print("=" * 80)

results_summary = []

for symbol in symbols:
    print(f"\n[F&O Audit] Evaluating 9-Model Ensemble for: {symbol}...")
    t0 = time.time()
    try:
        res = train_full_ensemble(
            symbol=symbol,
            days=365,
            save_dir=f"/tmp/models_fno_{symbol}",
            upload_gcs=False,
            run_cv=True
        )
        elapsed = round(time.time() - t0, 2)
        metrics = res.get("metrics", {})
        ens_metrics = metrics.get("ensemble", {})
        xgb_metrics = metrics.get("xgboost", {})
        lgb_metrics = metrics.get("lightgbm", {})
        cat_metrics = metrics.get("catboost", {})
        et_metrics  = metrics.get("extra_trees", {})

        row = {
            "Symbol": symbol,
            "Ensemble Accuracy": f"{ens_metrics.get('accuracy', 0.0)*100:.2f}%" if "accuracy" in ens_metrics else "N/A",
            "Ensemble F1": f"{ens_metrics.get('f1', 0.0):.4f}" if "f1" in ens_metrics else "N/A",
            "XGBoost Acc": f"{xgb_metrics.get('accuracy', 0.0)*100:.2f}%" if "accuracy" in xgb_metrics else "N/A",
            "LightGBM Acc": f"{lgb_metrics.get('accuracy', 0.0)*100:.2f}%" if "accuracy" in lgb_metrics else "N/A",
            "CatBoost Acc": f"{cat_metrics.get('accuracy', 0.0)*100:.2f}%" if "accuracy" in cat_metrics else "N/A",
            "ExtraTrees Acc": f"{et_metrics.get('accuracy', 0.0)*100:.2f}%" if "accuracy" in et_metrics else "N/A",
            "Train Samples": res.get("samples_train", 0),
            "Test Samples": res.get("samples_test", 0),
            "Elapsed (s)": elapsed
        }
        results_summary.append(row)
        print(f"   ✅ {symbol} -> Ensemble Accuracy: {row['Ensemble Accuracy']} | F1: {row['Ensemble F1']} ({elapsed}s)")
    except Exception as e:
        print(f"   ❌ Error evaluating {symbol}: {e}")

print("\n" + "=" * 80)
print("📊 FINAL AUDIT TABLE: F&O ACCURACY METRICS")
print("=" * 80)

df_results = pd.DataFrame(results_summary)
print(df_results.to_markdown(index=False))
