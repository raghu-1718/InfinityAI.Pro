"""
InfinityAI.Pro — Options Microstructure Feature Engineering
=============================================================
Calculates institutional order flow and options market maker features:
1. Gamma Exposure (GEX): Dealer delta-hedging exposure acceleration
2. Put-Call Ratio (PCR) Momentum: Rate of change of institutional hedging velocity
3. Implied Volatility (IV) Skew: 25-delta Put vs Call IV tail risk premium
4. Order Book Depth Imbalance (OBI): Level-2 bid/ask liquidity pressure
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple

def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

def calculate_black_scholes_gamma(
    spot: float,
    strike: float,
    tte_years: float = 0.015,  # ~5.5 days default for weekly index options
    iv: float = 0.15,
    r: float = 0.065
) -> float:
    """Calculates Black-Scholes Gamma."""
    if spot <= 0 or strike <= 0 or tte_years <= 0 or iv <= 0:
        return 0.0
    try:
        d1 = (math.log(spot / strike) + (r + 0.5 * iv * iv) * tte_years) / (iv * math.sqrt(tte_years))
        gamma = norm_pdf(d1) / (spot * iv * math.sqrt(tte_years))
        return gamma
    except Exception:
        return 0.0

def calculate_gamma_exposure(
    df_options: pd.DataFrame,
    spot_price: float
) -> float:
    """
    Calculates aggregate Dealer Gamma Exposure (GEX) across option chain.
    GEX = sum((Spot - Strike) * Open_Interest * Gamma * 100)
    Positive GEX = Market makers dampen volatility (mean-reversion).
    Negative GEX = Market makers accelerate volatility (trending breakout).
    """
    if df_options.empty or spot_price <= 0:
        return 0.0

    total_gex = 0.0
    for _, row in df_options.iterrows():
        strike = float(row.get('strike_price', spot_price))
        oi = float(row.get('open_interest', 0))
        iv = float(row.get('implied_volatility', 0.15))
        if iv <= 0 or np.isnan(iv):
            iv = 0.15
        
        gamma = calculate_black_scholes_gamma(spot=spot_price, strike=strike, iv=iv)
        # Call GEX is positive for market makers, Put GEX is negative
        opt_type = str(row.get('option_type', 'CE')).upper()
        sign = 1.0 if 'CE' in opt_type or 'CALL' in opt_type else -1.0
        
        # Dollar/Rupee Gamma per 1% move
        contract_gex = sign * (spot_price - strike) * oi * gamma * 100.0
        total_gex += contract_gex

    # Normalize to millions
    return round(total_gex / 1e6, 4)

def calculate_pcr_momentum(pcr_series: pd.Series, window: int = 20) -> pd.Series:
    """
    Calculates Put-Call Ratio (PCR) Momentum:
    (PCR_t - PCR_{t-5}) / sigma(PCR_20)
    """
    pcr_clean = pcr_series.ffill().fillna(1.0)
    pcr_delta_5 = pcr_clean - pcr_clean.shift(5)
    rolling_std = pcr_clean.rolling(window=window, min_periods=5).std().replace(0, np.nan)
    pcr_mom = (pcr_delta_5 / rolling_std).fillna(0.0)
    return pcr_mom

def calculate_iv_skew(df_options: pd.DataFrame, spot_price: float) -> float:
    """
    Calculates Implied Volatility Skew:
    IV(OTM Put ~ 25 Delta) - IV(OTM Call ~ 25 Delta)
    Higher skew = Institutional panic buying puts for protection.
    """
    if df_options.empty or spot_price <= 0:
        return 0.0

    otm_puts = df_options[
        (df_options['option_type'].str.contains('PE|PUT', case=False, na=False)) &
        (df_options['strike_price'] < spot_price)
    ]
    otm_calls = df_options[
        (df_options['option_type'].str.contains('CE|CALL', case=False, na=False)) &
        (df_options['strike_price'] > spot_price)
    ]

    put_iv = otm_puts['implied_volatility'].median() if not otm_puts.empty else 0.15
    call_iv = otm_calls['implied_volatility'].median() if not otm_calls.empty else 0.15

    if np.isnan(put_iv) or put_iv <= 0:
        put_iv = 0.15
    if np.isnan(call_iv) or call_iv <= 0:
        call_iv = 0.15

    return round(float(put_iv - call_iv), 4)

def calculate_order_book_imbalance(
    bid_qty_total: float,
    ask_qty_total: float
) -> float:
    """
    Calculates Order Book Depth Imbalance (OBI) from Level-2 Market Depth:
    OBI = (Total_Bid_Qty - Total_Ask_Qty) / (Total_Bid_Qty + Total_Ask_Qty)
    Range: [-1.0 (heavy supply) to +1.0 (heavy demand)].
    """
    denom = bid_qty_total + ask_qty_total
    if denom <= 0:
        return 0.0
    obi = (bid_qty_total - ask_qty_total) / denom
    return float(np.clip(round(obi, 4), -1.0, 1.0))

def enrich_dataset_with_microstructure(
    df: pd.DataFrame,
    df_options: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, list]:
    """
    Enriches dataset with GEX, PCR Momentum, IV Skew, and OBI features,
    handling edge cases with rolling median imputation and forward-fill protection.
    """
    data = df.copy()
    added_cols = []

    if 'close' not in data.columns:
        return data, []

    # 1. PCR & PCR Momentum
    if 'PCR' not in data.columns:
        if df_options is not None and not df_options.empty:
            pe_oi = df_options[df_options['option_type'].str.contains('PE', na=False)]['open_interest'].sum()
            ce_oi = df_options[df_options['option_type'].str.contains('CE', na=False)]['open_interest'].sum()
            pcr_val = pe_oi / ce_oi if ce_oi > 0 else 1.0
            data['PCR'] = pcr_val
        else:
            data['PCR'] = 1.0

    data['pcr_momentum'] = calculate_pcr_momentum(data['PCR'], window=20)
    added_cols.extend(['PCR', 'pcr_momentum'])

    # 2. GEX & IV Skew
    if df_options is not None and not df_options.empty:
        mean_spot = data['close'].mean()
        gex_val = calculate_gamma_exposure(df_options, mean_spot)
        iv_skew_val = calculate_iv_skew(df_options, mean_spot)
    else:
        gex_val = 0.0
        iv_skew_val = 0.01

    data['gex'] = gex_val
    data['iv_skew'] = iv_skew_val
    added_cols.extend(['gex', 'iv_skew'])

    # 3. Order Book Depth Imbalance (derived from volume velocity proxy if raw depth unavailable)
    if 'bid_qty' in data.columns and 'ask_qty' in data.columns:
        data['obi'] = (data['bid_qty'] - data['ask_qty']) / (data['bid_qty'] + data['ask_qty'] + 1e-6)
    else:
        # High-frequency tick volume imbalance proxy
        vol = data['volume'] if 'volume' in data.columns else pd.Series(1000, index=data.index)
        ret = data['close'].pct_change().fillna(0)
        data['obi'] = np.clip(np.sign(ret) * (vol / (vol.rolling(10).mean() + 1e-6) - 1.0), -1.0, 1.0)
        
    added_cols.append('obi')

    # Rolling median imputation for NaN / Inf
    for col in added_cols:
        data[col] = data[col].replace([np.inf, -np.inf], np.nan)
        data[col] = data[col].fillna(data[col].rolling(10, min_periods=1).median()).ffill().bfill().fillna(0.0)

    return data, added_cols
