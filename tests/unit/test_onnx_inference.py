"""
Unit Tests for Tri-Model ONNX Runtime Inference & Converter
InfinityAI.Pro - Production Verification Suite
"""
import pytest
import os
import sys
import subprocess
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "trained_models"

# Add engine-b to sys.path
engine_b_path = PROJECT_ROOT / "backend" / "engine-b"
if str(engine_b_path) not in sys.path:
    sys.path.insert(0, str(engine_b_path))
if str(engine_b_path / "src") not in sys.path:
    sys.path.insert(0, str(engine_b_path / "src"))


def test_onnx_artifacts_exist():
    """Verify that ONNX model binaries exist for NIFTY, BANKNIFTY, FINNIFTY, SENSEX Tri-Model ensembles."""
    for sym in ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]:
        for model_name in ["catboost", "lightgbm", "xgboost"]:
            onnx_file = MODELS_DIR / f"{sym}_{model_name}.onnx"
            assert onnx_file.exists(), f"Missing ONNX model artifact: {onnx_file.name}"
            assert onnx_file.stat().st_size > 0, f"Empty ONNX model artifact: {onnx_file.name}"


def test_onnx_inference_latency_sub_3ms():
    """Verify that ONNX Runtime inference achieves sub-3ms execution for Tri-Model ensemble."""
    venv_py = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    benchmark_script = PROJECT_ROOT / "tools" / "benchmark_onnx_inference.py"
    
    if venv_py.exists() and benchmark_script.exists():
        result = subprocess.run(
            [str(venv_py), str(benchmark_script)],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        assert result.returncode == 0, f"Benchmark script failed: {result.stderr}"
        assert result.stdout is not None
        assert ("PASSED (< 3.0ms)" in result.stdout) or ("VERIFICATION PASSED" in result.stdout)
    else:
        pytest.skip("Venv python or benchmark script not found")


def test_tri_model_onnx_converter_class():
    """Verify TriModelONNXConverter is importable and configured."""
    from ml.models.onnx_converter import TriModelONNXConverter
    converter = TriModelONNXConverter(str(MODELS_DIR))
    assert converter.models_dir == MODELS_DIR
