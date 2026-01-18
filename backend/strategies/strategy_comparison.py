"""
Strategy Comparison & Analysis Report
Tests multiple strategies and compares their performance
"""
import sys
sys.path.append('.')
from rsi_strategy import RSIStrategy, generate_sample_data
from ma_crossover import MAStrategy
import pandas as pd

def test_all_strategies():
    """Test all strategies and compare results"""
    print("=" * 80)
    print("  STRATEGY COMPARISON & ACCURACY ANALYSIS")
    print("=" * 80)
    
    # Test instruments
    instruments = ["RELIANCE", "NIFTY", "BANKNIFTY", "TCS", "HDFC"]
   
    all_results = []
    
    for symbol in instruments:
        print(f"\n\n{'='*80}")
        print(f"  TESTING: {symbol}")
        print(f"{'='*80}")
        
        # Generate data
        df = generate_sample_data(symbol, days=365)
        
        # Test RSI Strategy
        print(f"\n[1/2] Testing RSI Strategy...")
        rsi_strat = RSIStrategy(period=14, oversold=30, overbought=70)
        rsi_results = rsi_strat.backtest(df, initial_capital=100000)
        
        # Test MA Crossover
        print(f"[2/2] Testing MA Crossover...")
        ma_strat = MAStrategy(fast_period=9, slow_period=21)
        ma_results = ma_strat.backtest(df, initial_capital=100000)
        
        all_results.append({
            'instrument': symbol,
            'rsi_accuracy': rsi_results['accuracy'],
            'rsi_return': rsi_results['total_return'],
            'rsi_trades': rsi_results['total_trades'],
            'ma_accuracy': ma_results['accuracy'],
            'ma_return': ma_results['total_return'],
            'ma_trades': ma_results['total_trades']
        })
    
    # Create comparison DataFrame
    df_results = pd.DataFrame(all_results)
    
    print("\n\n" + "=" * 80)
    print("  FINAL RESULTS - STRATEGY ACCURACY COMPARISON")
    print("=" * 80)
    
    print("\n" + str(df_results.to_string(index=False)))
    
    # Calculate averages
    print("\n\nAVERAGE PERFORMANCE:")
    print(f"  RSI Strategy:")
    print(f"    Average Accuracy: {df_results['rsi_accuracy'].mean():.2f}%")
    print(f"    Average Return: {df_results['rsi_return'].mean():.2f}%")
    print(f"    Avg Trades: {df_results['rsi_trades'].mean():.1f}")
    
    print(f"\n  MA Crossover:")
    print(f"    Average Accuracy: {df_results['ma_accuracy'].mean():.2f}%")
    print(f"    Average Return: {df_results['ma_return'].mean():.2f}%")
    print(f"    Avg Trades: {df_results['ma_trades'].mean():.1f}")
    
    # Determine best strategy
    rsi_avg_acc = df_results['rsi_accuracy'].mean()
    ma_avg_acc = df_results['ma_accuracy'].mean()
    
    print("\n" + "=" * 80)
    if rsi_avg_acc > ma_avg_acc:
        print(f"  WINNER: RSI Strategy ({rsi_avg_acc:.2f}% vs {ma_avg_acc:.2f}%)")
    else:
        print(f"  WINNER: MA Crossover ({ma_avg_acc:.2f}% vs {rsi_avg_acc:.2f}%)")
    print("=" * 80)
    
    return df_results

if __name__ == "__main__":
    test_all_strategies()
