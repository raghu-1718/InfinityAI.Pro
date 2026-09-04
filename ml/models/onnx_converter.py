"""
InfinityAI.Pro — Tri-Model Ensemble ONNX Converter
===================================================
Exports CatBoost, LightGBM, and XGBoost models to highly optimized
ONNX binaries (.onnx) for sub-3ms ultra-low latency execution via ONNX Runtime.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import joblib

logger = logging.getLogger("InfinityAI.ONNXConverter")

try:
    import onnx
    import onnxruntime as ort
    import onnxmltools
    from onnxmltools.convert.common.data_types import FloatTensorType
    ONNX_AVAILABLE = True
except ImportError as e:
    ONNX_AVAILABLE = False
    logger.warning(f"ONNX conversion libraries not fully available: {e}")


class TriModelONNXConverter:
    """Institutional ONNX Converter for Tri-Model Quantitative Ensemble"""

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            self.models_dir = Path(__file__).resolve().parent.parent.parent / "trained_models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def convert_catboost(self, model: Any, output_path: Path) -> bool:
        """Converts CatBoost Classifier/Regressor to ONNX format natively."""
        try:
            model.save_model(str(output_path), format="onnx")
            logger.info(f"✅ CatBoost ONNX export successful: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"❌ CatBoost ONNX export failed: {e}")
            return False

    def convert_lightgbm(self, model: Any, output_path: Path, n_features: int = 20) -> bool:
        """Converts LightGBM Classifier/Regressor to ONNX via onnxmltools."""
        try:
            initial_types = [("input", FloatTensorType([None, n_features]))]
            # Handle Booster vs sklearn LGBMModel
            target_model = getattr(model, "booster_", model)
            onnx_model = onnxmltools.convert_lightgbm(
                target_model,
                initial_types=initial_types,
                target_opset=15
            )
            onnxmltools.utils.save_model(onnx_model, str(output_path))
            logger.info(f"✅ LightGBM ONNX export successful: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"❌ LightGBM ONNX export failed: {e}")
            return False

    def convert_xgboost(self, model: Any, output_path: Path, n_features: int = 20) -> bool:
        """Converts XGBoost Classifier/Regressor to ONNX via onnxmltools."""
        try:
            # Resolve underlying Booster and sanitize feature names to f0..fn
            if hasattr(model, "get_booster"):
                booster = model.get_booster()
            else:
                booster = model

            feat_count = n_features
            if hasattr(booster, "feature_names") and booster.feature_names:
                feat_count = len(booster.feature_names)
            booster.feature_names = [f"f{i}" for i in range(feat_count)]

            initial_types = [("input", FloatTensorType([None, feat_count]))]
            onnx_model = onnxmltools.convert_xgboost(
                booster,
                initial_types=initial_types,
                target_opset=15
            )
            onnxmltools.utils.save_model(onnx_model, str(output_path))
            logger.info(f"✅ XGBoost ONNX export successful: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"❌ XGBoost ONNX export failed: {e}")
            return False

    def convert_all_vaulted_symbols(
        self,
        symbols: Optional[List[str]] = None,
        default_features: int = 20
    ) -> Dict[str, Dict[str, bool]]:
        """Scans trained_models/ and converts all vaulted model artifacts."""
        if not ONNX_AVAILABLE:
            raise RuntimeError("Cannot convert models: onnx / onnxmltools libraries are missing.")

        target_symbols = symbols or ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "CRUDEOIL", "GOLD"]
        results: Dict[str, Dict[str, bool]] = {}

        for sym in target_symbols:
            results[sym] = {}
            logger.info(f"🔄 Converting Tri-Model ensemble for {sym}...")

            # 1. CatBoost
            cb_pkl = self.models_dir / f"{sym}_catboost_model.pkl"
            cb_out = self.models_dir / f"{sym}_catboost.onnx"
            if cb_pkl.exists():
                try:
                    cb_model = joblib.load(cb_pkl)
                    results[sym]["catboost"] = self.convert_catboost(cb_model, cb_out)
                except Exception as e:
                    logger.warning(f"Failed to load/convert {cb_pkl.name}: {e}")
                    results[sym]["catboost"] = False

            # 2. LightGBM
            lgb_pkl = self.models_dir / f"{sym}_lightgbm_model.pkl"
            lgb_out = self.models_dir / f"{sym}_lightgbm.onnx"
            if lgb_pkl.exists():
                try:
                    lgb_model = joblib.load(lgb_pkl)
                    n_feats = getattr(lgb_model, "n_features_in_", default_features)
                    results[sym]["lightgbm"] = self.convert_lightgbm(lgb_model, lgb_out, n_features=n_feats)
                except Exception as e:
                    logger.warning(f"Failed to load/convert {lgb_pkl.name}: {e}")
                    results[sym]["lightgbm"] = False

            # 3. XGBoost
            xgb_pkl = self.models_dir / f"{sym}_xgboost_model.pkl"
            xgb_out = self.models_dir / f"{sym}_xgboost.onnx"
            if xgb_pkl.exists():
                try:
                    xgb_model = joblib.load(xgb_pkl)
                    n_feats = getattr(xgb_model, "n_features_in_", default_features)
                    results[sym]["xgboost"] = self.convert_xgboost(xgb_model, xgb_out, n_features=n_feats)
                except Exception as e:
                    logger.warning(f"Failed to load/convert {xgb_pkl.name}: {e}")
                    results[sym]["xgboost"] = False

        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    converter = TriModelONNXConverter()
    conversion_res = converter.convert_all_vaulted_symbols()
    print("\n=== CONVERSION SUMMARY ===")
    for sym, res in conversion_res.items():
        print(f"{sym}: {res}")
