"""
InfinityAI.Pro — Institutional Triple Barrier Labeling & Sample Weighting Engine
================================================================================
Implements Marcos López de Prado's Triple Barrier Method (Advances in Financial Machine Learning):
1. Upper Barrier (Take Profit): Spot + (pt_multiplier * ATR_14)
2. Lower Barrier (Stop Loss): Spot - (sl_multiplier * ATR_14)
3. Vertical Barrier (Time Expiry): Maximum intraday holding window (e.g. 30 to 45 bars)
4. Sample Uniqueness & Return-Scaled Sample Weights: Scales training gradients by absolute realized return.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR)."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    return atr

def apply_triple_barrier_labeling(
    df: pd.DataFrame,
    pt_multiplier: float = 1.5,
    sl_multiplier: float = 1.0,
    max_holding_bars: int = 30
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Applies the Triple Barrier Method to label financial time series data.
    
    Parameters:
    - df: DataFrame containing 'high', 'low', 'close', and optionally 'atr'
    - pt_multiplier: Multiple of ATR for Upper Barrier (Take Profit)
    - sl_multiplier: Multiple of ATR for Lower Barrier (Stop Loss)
    - max_holding_bars: Maximum holding window before time barrier triggers
    
    Returns:
    - labeled_df: DataFrame with added columns:
        * 'target': 2 (BUY/Upper hit), 0 (SELL/Lower hit), 1 (HOLD/Vertical time expiry)
        * 'barrier_hit': 'UPPER', 'LOWER', or 'VERTICAL'
        * 'bars_held': Number of bars until barrier touch
        * 'realized_ret': Return achieved at barrier touch
        * 'sample_weight': Normalized return-scaled sample weight for gradient boosting
    - sample_weights: Series of normalized sample weights
    """
    data = df.copy()
    n = len(data)
    
    if 'atr' not in data.columns:
        data['atr'] = calculate_atr(data, period=14)
        
    atr = data['atr'].values
    close = data['close'].values
    high = data['high'].values
    low = data['low'].values
    
    targets = np.ones(n, dtype=int)  # 1 = HOLD default
    barrier_hits = ['VERTICAL'] * n
    bars_held = np.full(n, max_holding_bars, dtype=int)
    realized_rets = np.zeros(n, dtype=float)
    
    for i in range(n):
        curr_close = close[i]
        curr_atr = atr[i]
        if np.isnan(curr_atr) or curr_atr <= 0:
            curr_atr = curr_close * 0.01  # 1% fallback
            
        upper_barrier = curr_close + (pt_multiplier * curr_atr)
        lower_barrier = curr_close - (sl_multiplier * curr_atr)
        
        horizon = min(n, i + max_holding_bars + 1)
        hit = False
        
        for j in range(i + 1, horizon):
            bar_high = high[j]
            bar_low = low[j]
            
            # Check Upper Barrier (Take Profit hit -> BUY outcome)
            if bar_high >= upper_barrier:
                targets[i] = 2  # BUY
                barrier_hits[i] = 'UPPER'
                bars_held[i] = j - i
                realized_rets[i] = (upper_barrier - curr_close) / curr_close
                hit = True
                break
                
            # Check Lower Barrier (Stop Loss hit -> SELL outcome)
            if bar_low <= lower_barrier:
                targets[i] = 0  # SELL
                barrier_hits[i] = 'LOWER'
                bars_held[i] = j - i
                realized_rets[i] = (lower_barrier - curr_close) / curr_close
                hit = True
                break
                
        if not hit:
            # Vertical barrier reached
            last_idx = min(n - 1, i + max_holding_bars)
            targets[i] = 1  # HOLD / NEUTRAL
            barrier_hits[i] = 'VERTICAL'
            bars_held[i] = last_idx - i
            realized_rets[i] = (close[last_idx] - curr_close) / curr_close

    data['target'] = targets
    data['barrier_hit'] = barrier_hits
    data['bars_held'] = bars_held
    data['realized_ret'] = realized_rets
    
    # ── Sample Weighting: Volatility-Adjusted Realized Return ──
    # Higher momentum trend legs receive proportionally higher gradient weights
    atr_pct = (data['atr'] / data['close']).replace(0, 0.01).values
    raw_weights = np.abs(realized_rets) / np.maximum(atr_pct, 1e-4)
    
    # Add uniqueness boost (shorter holding bars = sharper impulse move)
    time_decay = 1.0 / np.sqrt(np.maximum(bars_held, 1))
    raw_weights = raw_weights * (1.0 + time_decay)
    
    # Normalize weights so mean is 1.0, bounded in [0.2, 5.0]
    mean_w = np.mean(raw_weights) if np.mean(raw_weights) > 0 else 1.0
    normalized_weights = np.clip(raw_weights / mean_w, 0.20, 5.0)
    
    data['sample_weight'] = normalized_weights
    return data, pd.Series(normalized_weights, index=data.index)
