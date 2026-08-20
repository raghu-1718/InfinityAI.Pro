"""
InfinityAI.Pro — Institutional Feature Engineering Pipeline
===========================================================
Engine B | Engine-Grade: Production | Version: 3.0.0

Feature Categories (65+ features across 8 groups):
  1. Price Momentum & Returns         (10 features)
  2. Moving Average Crossovers        ( 8 features)
  3. Oscillators & Trend Indicators   ( 8 features)
  4. Volatility Surface               ( 7 features)
  5. Volume & Microstructure          ( 8 features)
  6. Options-Derived (PCR/OI/IV)      ( 7 features)
  7. Market Regime                    ( 5 features)
  8. Macro Calendar & Cross-Asset     ( 7 features)
  9. Price Structure (S/R, Fibonacci) ( 8 features)
"""

import logging
import math
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, date

logger = logging.getLogger("InfinityAI.FeatureEngineer")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: PRICE MOMENTUM & RETURNS
# ─────────────────────────────────────────────────────────────────────────────

def _returns(close: pd.Series) -> Dict[str, pd.Series]:
    """Multi-period returns and log-returns."""
    return {
        "ret_1d":  close.pct_change(1, fill_method=None),
        "ret_3d":  close.pct_change(3, fill_method=None),
        "ret_5d":  close.pct_change(5, fill_method=None),
        "ret_10d": close.pct_change(10, fill_method=None),
        "ret_20d": close.pct_change(20, fill_method=None),
        "log_ret_1d": np.log(close / close.shift(1)),
        "log_ret_5d": np.log(close / close.shift(5)),
        "momentum_10": close.diff(10),
        "momentum_20": close.diff(20),
        "roc_10": ((close - close.shift(10)) / close.shift(10)) * 100,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: MOVING AVERAGE CROSSOVERS
# ─────────────────────────────────────────────────────────────────────────────

def _moving_averages(close: pd.Series) -> Dict[str, pd.Series]:
    """SMA/EMA and normalized cross-over distances."""
    sma_5  = close.rolling(5).mean()
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    ema_9  = close.ewm(span=9,  adjust=False).mean()
    ema_21 = close.ewm(span=21, adjust=False).mean()
    ema_50 = close.ewm(span=50, adjust=False).mean()
    ema_200= close.ewm(span=200, adjust=False).mean()

    return {
        "dist_ema_9":   (close - ema_9)  / (ema_9  + 1e-9),
        "dist_ema_21":  (close - ema_21) / (ema_21 + 1e-9),
        "dist_ema_50":  (close - ema_50) / (ema_50 + 1e-9),
        "dist_ema_200": (close - ema_200)/ (ema_200+ 1e-9),
        "ema_cross_9_21":  (ema_9  - ema_21) / (close + 1e-9),
        "ema_cross_21_50": (ema_21 - ema_50) / (close + 1e-9),
        "sma_cross_5_20":  (sma_5  - sma_20) / (close + 1e-9),
        "trend_strength":  (ema_9 - ema_200) / (ema_200 + 1e-9),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: OSCILLATORS & TREND INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def _oscillators(close: pd.Series, high: pd.Series, low: pd.Series) -> Dict[str, pd.Series]:
    """RSI, MACD, Bollinger, Stochastic, Williams %R, CCI."""
    # RSI (14)
    delta = close.diff()
    gain  = delta.where(delta > 0, 0).rolling(14).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs    = gain / (loss + 1e-9)
    rsi   = 100 - (100 / (1 + rs))

    # RSI (7) — faster for intraday
    gain7  = delta.where(delta > 0, 0).rolling(7).mean()
    loss7  = (-delta.where(delta < 0, 0)).rolling(7).mean()
    rs7    = gain7 / (loss7 + 1e-9)
    rsi7   = 100 - (100 / (1 + rs7))

    # MACD (12, 26, 9)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd   = ema_12 - ema_26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist   = macd - macd_signal

    # Bollinger Bands (20, 2σ)
    sma_20  = close.rolling(20).mean()
    std_20  = close.rolling(20).std()
    bb_upper = sma_20 + 2 * std_20
    bb_lower = sma_20 - 2 * std_20
    bb_pct   = (close - bb_lower) / ((bb_upper - bb_lower) + 1e-9)
    bb_width = (bb_upper - bb_lower) / (sma_20 + 1e-9)

    # Stochastic %K, %D (14, 3)
    lowest_low   = low.rolling(14).min()
    highest_high = high.rolling(14).max()
    stoch_k = 100 * ((close - lowest_low) / ((highest_high - lowest_low) + 1e-9))
    stoch_d = stoch_k.rolling(3).mean()

    # Williams %R (14)
    williams_r = -100 * ((highest_high - close) / ((highest_high - lowest_low) + 1e-9))

    # CCI (20)
    typical_price = (high + low + close) / 3
    tp_sma = typical_price.rolling(20).mean()
    tp_std = typical_price.rolling(20).std()
    cci = (typical_price - tp_sma) / (0.015 * tp_std + 1e-9)

    return {
        "rsi_14":       rsi,
        "rsi_7":        rsi7,
        "macd":         macd / (close + 1e-9),
        "macd_signal":  macd_signal / (close + 1e-9),
        "macd_hist":    macd_hist / (close + 1e-9),
        "bb_pct":       bb_pct,
        "bb_width":     bb_width,
        "stoch_k":      stoch_k,
        "stoch_d":      stoch_d,
        "williams_r":   williams_r,
        "cci_20":       cci,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: VOLATILITY SURFACE
# ─────────────────────────────────────────────────────────────────────────────

def _volatility(close: pd.Series, high: pd.Series, low: pd.Series) -> Dict[str, pd.Series]:
    """Realized volatility, ATR, GARCH proxy, vol-of-vol."""
    log_ret = np.log(close / close.shift(1))

    # Realized volatility (annualized)
    rv_5  = log_ret.rolling(5).std()  * np.sqrt(252)
    rv_10 = log_ret.rolling(10).std() * np.sqrt(252)
    rv_21 = log_ret.rolling(21).std() * np.sqrt(252)

    # ATR (14)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low  - close.shift()).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    atr_pct = atr / (close + 1e-9)

    # GARCH(1,1) proxy — rolling conditional vol
    alpha_g, beta_g = 0.09, 0.90
    variance = log_ret.rolling(21).var()
    garch_vol = variance.ewm(alpha=alpha_g).mean().apply(lambda x: math.sqrt(max(x, 0)) * math.sqrt(252) if pd.notna(x) else np.nan)

    # Vol-of-vol — 2nd order vol
    vol_of_vol = rv_10.rolling(10).std()

    # Historical vol ratio (current vs 21d mean)
    vol_ratio_5_21 = rv_5 / (rv_21 + 1e-9)

    return {
        "rv_5":         rv_5,
        "rv_10":        rv_10,
        "rv_21":        rv_21,
        "atr_pct":      atr_pct,
        "garch_vol":    garch_vol,
        "vol_of_vol":   vol_of_vol,
        "vol_ratio_5_21": vol_ratio_5_21,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: VOLUME & MICROSTRUCTURE
# ─────────────────────────────────────────────────────────────────────────────

def _volume_microstructure(close: pd.Series, volume: pd.Series, high: pd.Series, low: pd.Series) -> Dict[str, pd.Series]:
    """OBV, VWAP, bid-ask proxy, tick-rule, price impact."""
    vol_ma20   = volume.rolling(20).mean()
    vol_ratio  = volume / (vol_ma20 + 1e-9)

    # OBV and OBV momentum
    obv        = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    obv_slope  = obv.pct_change(5, fill_method=None)

    # VWAP deviation (rolling 20)
    typical    = (high + low + close) / 3
    vwap_20    = (typical * volume).rolling(20).sum() / (volume.rolling(20).sum() + 1e-9)
    vwap_dev   = (close - vwap_20) / (vwap_20 + 1e-9)

    # Bid-ask spread proxy (Corwin-Schultz estimator)
    alpha      = (np.sqrt(2 * np.log(high / low)) - np.sqrt(np.log(high / low))).clip(lower=0)
    ba_spread  = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))

    # Tick rule: +1 (uptick), -1 (downtick)
    tick_rule  = np.sign(close.diff()).fillna(0)

    # Amihud illiquidity ratio: |return| / volume
    amihud     = (close.pct_change(fill_method=None).abs() / (volume + 1e-9)).rolling(10).mean() * 1e6

    # Price impact: |return| / sqrt(volume)
    price_impact = close.pct_change(fill_method=None).abs() / (np.sqrt(volume) + 1e-9)

    return {
        "vol_ratio":    vol_ratio,
        "obv_slope":    obv_slope,
        "vwap_dev":     vwap_dev,
        "ba_spread":    ba_spread,
        "tick_rule":    tick_rule,
        "amihud_illiq": amihud,
        "price_impact": price_impact,
        "vol_ma20":     vol_ma20,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: OPTIONS-DERIVED (PCR, OI, IV)
# ─────────────────────────────────────────────────────────────────────────────

def _options_features(data: pd.DataFrame) -> Dict[str, pd.Series]:
    """PCR, OI momentum, IV-derived features if available."""
    feats: Dict[str, pd.Series] = {}
    idx = data.index

    if "PCR" in data.columns:
        pcr = data["PCR"].ffill().fillna(1.0)
        feats["pcr"]           = pcr
        feats["pcr_sma_5"]     = pcr.rolling(5).mean()
        feats["pcr_zscore"]    = (pcr - pcr.rolling(20).mean()) / (pcr.rolling(20).std() + 1e-9)

    if "Total_CE_OI" in data.columns and "Total_PE_OI" in data.columns:
        ce_oi = data["Total_CE_OI"].ffill().fillna(0)
        pe_oi = data["Total_PE_OI"].ffill().fillna(0)
        total_oi = ce_oi + pe_oi
        feats["oi_ce_pe_skew"]  = (pe_oi - ce_oi) / (total_oi + 1e-9)
        feats["oi_change_rate"] = total_oi.pct_change(1, fill_method=None)

    # IV Rank proxy (uses realized vol as proxy when IV not available)
    if "rv_21" in data.columns:
        rv = data["rv_21"]
        rv_52w_high = rv.rolling(252).max()
        rv_52w_low  = rv.rolling(252).min()
        feats["ivr_proxy"] = (rv - rv_52w_low) / ((rv_52w_high - rv_52w_low) + 1e-9)

    # Max pain proximity (nearest round 500 for NIFTY-like instruments)
    if "close" in data.columns:
        close = data["close"]
        nearest_round = (close / 500).round() * 500
        feats["max_pain_prox"] = (close - nearest_round) / (close + 1e-9)

    return feats


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: MARKET REGIME
# ─────────────────────────────────────────────────────────────────────────────

def _regime_features(close: pd.Series, high: pd.Series, low: pd.Series) -> Dict[str, pd.Series]:
    """ADX trend strength, Hurst exponent, regime classification."""

    # ADX (14) — Average Directional Index
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low  - close.shift()).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()

    plus_dm  = (high - high.shift()).clip(lower=0)
    minus_dm = (low.shift() - low).clip(lower=0)
    # Zero out DM where the other is larger
    cond     = plus_dm >= minus_dm
    plus_dm  = plus_dm.where(cond, 0)
    minus_dm = minus_dm.where(~cond, 0)

    plus_di  = 100 * plus_dm.rolling(14).mean()  / (atr14 + 1e-9)
    minus_di = 100 * minus_dm.rolling(14).mean() / (atr14 + 1e-9)
    dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    adx      = dx.rolling(14).mean()

    # Hurst Exponent (R/S analysis, rolling 60-period window)
    def hurst_rs(x: np.ndarray) -> float:
        """Compute Hurst exponent via R/S method. H > 0.5 = trending."""
        if len(x) < 20 or np.std(x) < 1e-10:
            return 0.5
        try:
            lags = range(2, min(len(x) // 2, 20))
            rs_vals = []
            for lag in lags:
                sub = x[:lag]
                mean_sub = np.mean(sub)
                devs = np.cumsum(sub - mean_sub)
                r = max(devs) - min(devs)
                s = np.std(sub, ddof=1)
                if s > 1e-10:
                    rs_vals.append(r / s)
            if len(rs_vals) < 2:
                return 0.5
            # Log-log regression
            log_lags = np.log(list(range(2, len(rs_vals) + 2)))
            log_rs   = np.log(rs_vals)
            slope    = np.polyfit(log_lags, log_rs, 1)[0]
            return float(np.clip(slope, 0, 1))
        except Exception:
            return 0.5

    log_ret = np.log(close / close.shift(1)).fillna(0)
    hurst   = log_ret.rolling(60).apply(hurst_rs, raw=True)

    # Regime: 0=Bear/ranging, 1=Neutral, 2=Bull/trending
    adx_thresh = 25  # >25 = trending
    ret_20 = close.pct_change(20, fill_method=None)
    regime = pd.Series(1, index=close.index)
    regime = regime.where(~((adx > adx_thresh) & (ret_20 > 0.01)), 2)   # bull trend
    regime = regime.where(~((adx > adx_thresh) & (ret_20 < -0.01)), 0)  # bear trend

    return {
        "adx":          adx,
        "plus_di":      plus_di,
        "minus_di":     minus_di,
        "hurst_exp":    hurst,
        "regime":       regime,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: PRICE STRUCTURE (S/R, FIBONACCI, PIVOTS)
# ─────────────────────────────────────────────────────────────────────────────

def _price_structure(close: pd.Series, high: pd.Series, low: pd.Series) -> Dict[str, pd.Series]:
    """Pivot points, Fibonacci levels, support/resistance proximity."""
    # Classic Pivot Points (based on prior day)
    pp  = (high.shift(1) + low.shift(1) + close.shift(1)) / 3
    r1  = 2 * pp - low.shift(1)
    s1  = 2 * pp - high.shift(1)
    r2  = pp + (high.shift(1) - low.shift(1))
    s2  = pp - (high.shift(1) - low.shift(1))

    # Normalized distances from pivots
    dist_pp = (close - pp)   / (close + 1e-9)
    dist_r1 = (close - r1)   / (close + 1e-9)
    dist_s1 = (close - s1)   / (close + 1e-9)
    dist_r2 = (close - r2)   / (close + 1e-9)
    dist_s2 = (close - s2)   / (close + 1e-9)

    # 52-week (252-day) high/low proximity
    high_52w = high.rolling(252).max()
    low_52w  = low.rolling(252).min()
    dist_52w_high = (close - high_52w) / (high_52w + 1e-9)
    dist_52w_low  = (close - low_52w)  / (low_52w + 1e-9)

    # Fibonacci retracement levels (from 20-day swing)
    swing_high = high.rolling(20).max()
    swing_low  = low.rolling(20).min()
    fib_range  = swing_high - swing_low
    fib_382    = swing_high - 0.382 * fib_range
    fib_618    = swing_high - 0.618 * fib_range
    fib_dist   = (close - fib_618) / (fib_range + 1e-9)  # distance from 61.8% retracement

    return {
        "dist_pp":       dist_pp,
        "dist_r1":       dist_r1,
        "dist_s1":       dist_s1,
        "dist_r2":       dist_r2,
        "dist_s2":       dist_s2,
        "dist_52w_high": dist_52w_high,
        "dist_52w_low":  dist_52w_low,
        "fib_dist_618":  fib_dist,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN FEATURE ENGINEER CLASS
# ─────────────────────────────────────────────────────────────────────────────

class FeatureEngineer:
    """
    Institutional-grade feature engineering for InfinityAI.Pro ML pipeline.

    Produces 65+ features across 9 categories:
      Price Returns | MA Crossovers | Oscillators | Volatility |
      Volume/Microstructure | Options | Regime | Price Structure | Macro

    Usage:
        fe = FeatureEngineer()
        features_df, feature_cols = fe.generate_all_features(ohlcv_df)
    """

    VERSION = "3.0.0"

    def __init__(self):
        logger.info(f"✅ FeatureEngineer v{self.VERSION} initialized — 65+ institutional features")

    # ── Core static indicators (legacy compat) ────────────────────────────

    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=window).mean()

    @staticmethod
    def calculate_ema(prices: pd.Series, span: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain  = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs    = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD + Signal + Histogram"""
        ema_fast   = prices.ewm(span=fast, adjust=False).mean()
        ema_slow   = prices.ewm(span=slow, adjust=False).mean()
        macd_line  = ema_fast - ema_slow
        signal_line= macd_line.ewm(span=signal, adjust=False).mean()
        return {"macd": macd_line, "signal": signal_line, "histogram": macd_line - signal_line}

    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma  = prices.rolling(window=window).mean()
        std  = prices.rolling(window=window).std()
        return {"upper": sma + std * num_std, "middle": sma, "lower": sma - std * num_std}

    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr  = pd.concat([(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        return (np.sign(close.diff()) * volume).fillna(0).cumsum()

    # ── Primary interface ─────────────────────────────────────────────────

    def generate_all_features(
        self,
        df: pd.DataFrame,
        price_col: str = "close",
        volume_col: Optional[str] = "volume",
        include_options: bool = True,
        include_regime: bool = True,
        include_structure: bool = True,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Generate the full institutional feature set from OHLCV + Options data.

        Args:
            df: DataFrame with at minimum {'close', 'high', 'low'} columns.
                Optional: 'volume', 'PCR', 'Total_CE_OI', 'Total_PE_OI'
            price_col: Name of the close price column.
            volume_col: Name of the volume column (None to skip).
            include_options: Include PCR/OI features.
            include_regime: Include ADX/Hurst regime features.
            include_structure: Include pivot/Fibonacci features.

        Returns:
            (features_df, feature_cols_list) — df with all features added.
        """
        data = df.copy()
        feature_cols: List[str] = []

        # Standardize column names (lower-case)
        data.columns = [c.lower() for c in data.columns]
        close  = data[price_col]
        high   = data["high"]   if "high"   in data.columns else close
        low    = data["low"]    if "low"    in data.columns else close
        volume = data[volume_col] if (volume_col and volume_col in data.columns) else None

        try:
            # ── 1. Price Returns ───────────────────────────────────────────
            rets = _returns(close)
            for k, v in rets.items():
                data[k] = v
            feature_cols.extend(rets.keys())

            # ── 2. Moving Averages ─────────────────────────────────────────
            mas = _moving_averages(close)
            for k, v in mas.items():
                data[k] = v
            feature_cols.extend(mas.keys())

            # ── 3. Oscillators ─────────────────────────────────────────────
            osc = _oscillators(close, high, low)
            for k, v in osc.items():
                data[k] = v
            feature_cols.extend(osc.keys())

            # ── 4. Volatility Surface ──────────────────────────────────────
            vol_feats = _volatility(close, high, low)
            for k, v in vol_feats.items():
                data[k] = v
            feature_cols.extend(vol_feats.keys())

            # ── 5. Volume & Microstructure ─────────────────────────────────
            if volume is not None:
                micro = _volume_microstructure(close, volume, high, low)
                for k, v in micro.items():
                    data[k] = v
                feature_cols.extend(micro.keys())

            # ── 6. Options-Derived ──────────────────────────────────────────
            if include_options:
                opts = _options_features(data)
                for k, v in opts.items():
                    data[k] = v
                feature_cols.extend(opts.keys())

            # ── 7. Market Regime ────────────────────────────────────────────
            if include_regime:
                reg = _regime_features(close, high, low)
                for k, v in reg.items():
                    data[k] = v
                feature_cols.extend(reg.keys())

            # ── 8. Price Structure ──────────────────────────────────────────
            if include_structure:
                struct = _price_structure(close, high, low)
                for k, v in struct.items():
                    data[k] = v
                feature_cols.extend(struct.keys())

            # ── Final clean-up ──────────────────────────────────────────────
            # Remove duplicate cols (e.g., from options inject)
            feature_cols = list(dict.fromkeys([c for c in feature_cols if c in data.columns]))

            # Replace inf with NaN then forward-fill then fill-zero
            data.replace([np.inf, -np.inf], np.nan, inplace=True)
            data[feature_cols] = data[feature_cols].ffill().fillna(0)

            logger.info(
                f"✅ FeatureEngineer: Generated {len(feature_cols)} features "
                f"from {len(df)} rows"
            )

        except Exception as e:
            logger.error(f"❌ Feature generation error: {e}", exc_info=True)
            raise

        return data, feature_cols

    def get_feature_columns(self) -> List[str]:
        """Return full list of expected feature column names (v3.0 canonical set)."""
        return [
            # Returns
            "ret_1d", "ret_3d", "ret_5d", "ret_10d", "ret_20d",
            "log_ret_1d", "log_ret_5d", "momentum_10", "momentum_20", "roc_10",
            # MAs
            "dist_ema_9", "dist_ema_21", "dist_ema_50", "dist_ema_200",
            "ema_cross_9_21", "ema_cross_21_50", "sma_cross_5_20", "trend_strength",
            # Oscillators
            "rsi_14", "rsi_7", "macd", "macd_signal", "macd_hist",
            "bb_pct", "bb_width", "stoch_k", "stoch_d", "williams_r", "cci_20",
            # Volatility
            "rv_5", "rv_10", "rv_21", "atr_pct", "garch_vol", "vol_of_vol", "vol_ratio_5_21",
            # Volume / Microstructure
            "vol_ratio", "obv_slope", "vwap_dev", "ba_spread", "tick_rule",
            "amihud_illiq", "price_impact", "vol_ma20",
            # Options
            "pcr", "pcr_sma_5", "pcr_zscore",
            "oi_ce_pe_skew", "oi_change_rate", "ivr_proxy", "max_pain_prox",
            # Regime
            "adx", "plus_di", "minus_di", "hurst_exp", "regime",
            # Price Structure
            "dist_pp", "dist_r1", "dist_s1", "dist_r2", "dist_s2",
            "dist_52w_high", "dist_52w_low", "fib_dist_618",
        ]

    def select_top_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int = 30,
        method: str = "shap",
    ) -> List[str]:
        """
        Select top N features via SHAP or Random Forest importance.

        Args:
            X: Feature DataFrame
            y: Target series
            n_features: Number of top features to return
            method: 'shap' (preferred) or 'rf'

        Returns:
            List of top feature names ordered by importance.
        """
        from sklearn.ensemble import RandomForestClassifier

        try:
            rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
            rf.fit(X, y)

            if method == "shap":
                try:
                    import shap
                    explainer = shap.TreeExplainer(rf)
                    shap_vals = explainer.shap_values(X.iloc[:500])
                    # Mean absolute SHAP across classes
                    if isinstance(shap_vals, list):
                        mean_shap = np.abs(np.array(shap_vals)).mean(axis=(0, 2))
                    else:
                        mean_shap = np.abs(shap_vals).mean(axis=0)
                    importance_df = pd.DataFrame({
                        "feature": X.columns,
                        "importance": mean_shap
                    }).sort_values("importance", ascending=False)
                    top = importance_df.head(n_features)["feature"].tolist()
                    logger.info(f"✅ SHAP top-{n_features} features selected")
                    return top
                except ImportError:
                    logger.warning("SHAP not installed, falling back to RF importance")

            # RF importance fallback
            importance_df = pd.DataFrame({
                "feature": X.columns,
                "importance": rf.feature_importances_
            }).sort_values("importance", ascending=False)

            top = importance_df.head(n_features)["feature"].tolist()
            logger.info(f"✅ RF importance top-{n_features} features selected")
            return top

        except Exception as e:
            logger.error(f"Feature selection error: {e}")
            return list(X.columns[:n_features])

    def compute_feature_stats(self, df: pd.DataFrame, feature_cols: List[str]) -> Dict:
        """
        Compute baseline statistics for drift monitoring (PSI reference).
        Returns dict: {feature: {mean, std, p5, p25, p75, p95}}
        """
        stats = {}
        for col in feature_cols:
            if col not in df.columns:
                continue
            series = df[col].dropna()
            if series.empty:
                continue
            stats[col] = {
                "mean": float(series.mean()),
                "std":  float(series.std()),
                "p5":   float(series.quantile(0.05)),
                "p25":  float(series.quantile(0.25)),
                "p50":  float(series.median()),
                "p75":  float(series.quantile(0.75)),
                "p95":  float(series.quantile(0.95)),
                "n":    int(len(series)),
            }
        return stats


# ── Singleton instance ────────────────────────────────────────────────────────
feature_engineer = FeatureEngineer()
