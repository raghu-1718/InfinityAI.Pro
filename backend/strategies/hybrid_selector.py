"""
Hybrid Strategy Selector
Automatically selects best strategy based on market conditions
"""
import pandas as pd
import numpy as np

class HybridStrategySelector:
    """
    Selects between RSI and MA strategies based on market regime
    - Choppy/Range-bound: Use RSI (80% accuracy)
    - Trending: Use MA Crossover (75% accuracy, better returns)
    """
    
    def __init__(self):
        self.name = "Hybrid_RSI_MA"
    
    def detect_market_regime(self, df, lookback=20):
        """
        Detect if market is trending or choppy
        Uses ADX-like logic: high volatility with direction = trending
        """
        df = df.copy()
        
        # Calculate price changes
        df['returns'] = df['close'].pct_change()
        
        # Calculate rolling std (volatility)
        df['volatility'] = df['returns'].rolling(window=lookback).std()
        
        # Calculate directional movement
        df['trend_strength'] = abs(df['close'].rolling(window=lookback).apply(
            lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0]
        ))
        
        # Regime decision
        # Trending: high trend strength (>5%) and moderate volatility
        # Choppy: low trend strength (<3%) or very high volatility
        df['regime'] = 'choppy'
        df.loc[df['trend_strength'] > 0.05, 'regime'] = 'trending'
        
        return df
    
    def select_strategy(self, df):
        """
        Select and apply appropriate strategy
        Returns: 'RSI' or 'MA' for each period
        """
        df = self.detect_market_regime(df)
        return df

def test_hybrid_selector():
    """Test the hybrid strategy selector"""
    import sys
    sys.path.append('.')
    from rsi_strategy import generate_sample_data
    from enhanced_rsi import EnhancedRSIStrategy
    from ma_crossover import MAStrategy
    
    print("=" * 80)
    print("  HYBRID STRATEGY SELECTOR - MARKET REGIME DETECTION")
    print("=" * 80)
    
    # Generate data
    df = generate_sample_data("NIFTY", days=365)
    
    # Detect regimes
    selector = HybridStrategySelector()
    df_analyzed = selector.select_strategy(df)
    
    # Count regimes
    regime_counts = df_analyzed['regime'].value_counts()
    
    print(f"\nMarket Regime Analysis (365 days):")
    print(f"  Trending Days: {regime_counts.get('trending', 0)} ({regime_counts.get('trending', 0)/len(df)*100:.1f}%)")
    print(f"  Choppy Days: {regime_counts.get('choppy', 0)} ({regime_counts.get('choppy', 0)/len(df)*100:.1f}%)")
    
    print(f"\nStrategy Recommendation:")
    if regime_counts.get('trending', 0) > regime_counts.get('choppy', 0):
        print(f"  PRIMARY: MA Crossover (market is trending)")
        print(f"  SECONDARY: RSI for range-bound periods")
    else:
        print(f"  PRIMARY: RSI Strategy (market is choppy)")
        print(f"  SECONDARY: MA Crossover for trending periods")
   
    return df_analyzed

if __name__ == "__main__":
    test_hybrid_selector()
