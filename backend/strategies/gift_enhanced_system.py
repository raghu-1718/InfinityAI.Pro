"""
GIFT Nifty Enhanced Strategy Integration
Combines existing strategies with GIFT Nifty pre-market signals
"""
import sys
sys.path.append('.')
from gift_nifty_signals import GIFTNiftySignalGenerator
from enhanced_rsi import EnhancedRSIStrategy
from ma_crossover import MAStrategy
from rsi_strategy import generate_sample_data

class GIFTEnhancedTradingSystem:
    """
    Complete trading system with GIFT Nifty integration
    """
    
    def __init__(self):
        self.gift_signal_gen = GIFTNiftySignalGenerator()
        self.rsi_strategy = None
        self.ma_strategy = None
        self.current_signal = None
    
    def morning_briefing(self, gift_nifty, nifty_prev_close):
        """
        Generate morning trading briefing based on GIFT Nifty
        Call this before market opens (before 9:15 AM)
        """
        print("\n" + "="*80)
        print("  MORNING TRADING BRIEFING")
        print("  " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*80)
        
        # Generate GIFT Nifty signal
        self.gift_signal_gen.fetch_gift_nifty_manual(gift_nifty, nifty_prev_close)
        self.current_signal = self.gift_signal_gen.generate_complete_signal()
        self.gift_signal_gen.print_signal_report(self.current_signal)
        
        # Initialize recommended strategy
        strategy_name = self.current_signal['recommended_strategy']
        
        if strategy_name == "RSI_MeanReversion":
            self.rsi_strategy = EnhancedRSIStrategy(
                period=14,
                oversold=30,
                overbought=70,
                stop_loss_pct=self.current_signal['stop_loss_pct'],
                take_profit_pct=3.0
            )
            print(f"\n[ACTIVE STRATEGY] Enhanced RSI Mean Reversion")
            print(f"  - Oversold threshold: 30")
            print(f"  - Stop Loss: {self.current_signal['stop_loss_pct']}%")
            print(f"  - Position Size Multiplier: {self.current_signal['position_size_multiplier']}")
        
        elif strategy_name == "MA_Crossover":
            self.ma_strategy = MAStrategy(fast_period=9, slow_period=21)
            print(f"\n[ACTIVE STRATEGY] Moving Average Crossover")
            print(f"  - Fast MA: 9")
            print(f"  - Slow MA: 21")
            print(f"  - Position Size Multiplier: {self.current_signal['position_size_multiplier']}")
        
        else:
            print(f"\n[ACTIVE STRATEGY] Hybrid Auto-Selector")
            print(f"  - Will choose based on intraday conditions")
        
        return self.current_signal
    
    def backtest_with_gift_nifty(self, symbol="NIFTY", gift_gap=0.5):
        """
        Backtest showing performance with GIFT Nifty signals
        """
        print(f"\n{'='*80}")
        print(f"  BACKTESTING WITH GIFT NIFTY INTEGRATION")
        print(f"{'='*80}")
        
        # Simulate GIFT Nifty gap
        print(f"\nSimulated GIFT Nifty GAP: {gift_gap:+.2f}%")
        
        # Generate sample data
        df = generate_sample_data(symbol, days=365)
        nifty_close = df.iloc[0]['close']
        gift_value = nifty_close * (1 + gift_gap/100)
        
       # Get signal
        self.gift_signal_gen.fetch_gift_nifty_manual(gift_value, nifty_close)
        signal = self.gift_signal_gen.generate_complete_signal()
        
        # Test recommended strategy
        strategy_name = signal['recommended_strategy']
        
        if "RSI" in strategy_name:
            print(f"\nTesting: Enhanced RSI Strategy")
            strategy = EnhancedRSIStrategy(
                stop_loss_pct=signal['stop_loss_pct']
            )
            results = strategy.backtest(
                df,
                position_size=0.15 * signal['position_size_multiplier']
            )
        else:
            print(f"\nTesting: MA Crossover Strategy")
            strategy = MAStrategy(fast_period=9, slow_period=21)
            results = strategy.backtest(
                df,
                position_size=0.20 * signal['position_size_multiplier']
            )
        
        # Display results
        print(f"\n{'='*80}")
        print(f"  BACKTEST RESULTS")
        print(f"{'='*80}")
        print(f"\nStrategy: {results['strategy_name']}")
        print(f"GIFT Nifty Signal: {signal['bias']} ({signal['gap_percent']:+.2f}%)")
        print(f"\nPerformance:")
        print(f"  Accuracy: {results['accuracy']}%")
        print(f"  Total Return: {results['total_return']}%")
        print(f"  Total Trades: {results['total_trades']}")
        print(f"  Winning: {results['winning_trades']}")
        
        return results

from datetime import datetime

def main():
    """Demo the complete GIFT Nifty enhanced system"""
    system = GIFTEnhancedTradingSystem()
    
    # Example 1: Morning briefing with bullish gap
    print("\n\n" + "="*80)
    print("  EXAMPLE 1: BULLISH MORNING GAP")
    print("  " + "="*80)
    
    system.morning_briefing(
        gift_nifty=23750,  # GIFT Nifty current
        nifty_prev_close=23500  # Nifty previous close
    )
    
    # Example 2: Backtest with different gap scenarios
    print("\n\n" + "="*80)
    print("  EXAMPLE 2: BACKTESTING WITH GIFT NIFTY")
    print("  " + "="*80)
    
    # Test with positive gap
    system.backtest_with_gift_nifty("NIFTY", gift_gap=+0.8)
    
    print("\n\n" + "="*80)
    print("  GIFT NIFTY INTEGRATION READY FOR USE")
    print("  " + "="*80)
    print("\nNext Steps:")
    print("  1. Each morning before 9:15 AM, check GIFT Nifty")
    print("  2. Run morning_briefing() with actual values")
    print("  3. Use recommended strategy for the day")
    print("  4. Adjust position sizes per signal")
    print("  5. Monitor performance improvements\n")

if __name__ == "__main__":
    main()
