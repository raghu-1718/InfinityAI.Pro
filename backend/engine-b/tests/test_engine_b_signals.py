import os
import sys
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

engine_b_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if engine_b_dir not in sys.path:
    sys.path.insert(0, engine_b_dir)

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from src.main import evaluate_option_signal_conviction, clean_floats


def test_evaluate_option_signal_conviction_adx_veto():
    """Verify that ADX < 15.0 properly triggers veto_triggered=True and signal=HOLD."""
    df_dummy = pd.DataFrame({
        "ADX_14": [13.5],
        "RSI_14": [55.0],
        "close": [24500.0],
        "EMA_200": [24000.0]
    })
    
    with patch("src.main.fetch_market_breadth_and_gift", return_value={"advance_decline_ratio": 1.2}):
        conviction = evaluate_option_signal_conviction(df_dummy, ml_probability=0.78)
        assert conviction["veto_triggered"] is True
        assert conviction["signal"] == "HOLD"
        assert "ADX <" in conviction["reason"]
        assert "ranging/consolidating" in conviction["reason"]


def test_evaluate_option_signal_conviction_pass():
    """Verify that high ADX (>25) and good breadth passes with directional signal."""
    df_dummy = pd.DataFrame({
        "ADX_14": [32.0],
        "RSI_14": [62.0],
        "close": [24500.0],
        "EMA_200": [24000.0]
    })
    
    with patch("src.main.fetch_market_breadth_and_gift", return_value={"advance_decline_ratio": 1.5}):
        conviction = evaluate_option_signal_conviction(df_dummy, ml_probability=0.72)
        assert conviction["veto_triggered"] is False
        assert conviction["signal"] == "BUY"
