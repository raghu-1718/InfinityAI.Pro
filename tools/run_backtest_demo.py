"""
Simple Backtest Example for Iron Condor Strategy
Uses sample data to demonstrate backtesting framework
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.options.backtester import OptionsBacktester
from backend.options.strategies.iron_condor import IronCondorStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sample_historical_data(days=30):
    """Create sample historical option data for testing"""
    data = []
    base_spot = 18000
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        
        # Simulate spot price movement
        spot = base_spot + np.random.randint(-200, 200)
        
        # Create option chain snapshot
        option_chain = []
        for strike in range(17700, 18400, 100):
            option_chain.append({
                'strike': strike,
                'call_oi': np.random.randint(5000, 30000),
                'put_oi': np.random.randint(5000, 30000),
                'call_ltp': max(strike - spot, 0) + np.random.randint(10, 100),
                'put_ltp': max(spot - strike, 0) + np.random.randint(10, 100)
            })
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'spot_price': spot,
            'option_chain': option_chain
        })
    
    return pd.DataFrame(data)

def iron_condor_backtest_strategy(spot, option_chain):
    """
    Sample Iron Condor strategy for backtesting
    Enter when VIX is low (simulated by OI analysis)
    """
    if len(option_chain) < 4:
        return None
    
    # Calculate simplified PCR
    total_call_oi = sum([opt.get('call_oi', 0) for opt in option_chain])
    total_put_oi = sum([opt.get('put_oi', 0) for opt in option_chain])
    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1
    
    # Enter Iron Condor when PCR is neutral (0.9 - 1.1)
    if 0.9 <= pcr <= 1.1:
        return {
            'type': 'Iron Condor',
            'entry_price': spot,
            'cost': 5000,  # Net premium received
            'value': 5000,  # Current value
            'target_profit': 15000,
            'max_loss': 5000,
            'profit': np.random.randint(-2000, 3000)  # Simulated P&L
        }
    
    return None

def run_backtest_demo():
    """Run backtest demonstration"""
    print("=" * 80)
    print("  IRON CONDOR BACKTEST DEMONSTRATION")
    print("=" * 80)
    
    # Create sample data
    print("\n[STEP 1] Generating sample historical data...")
    historical_data = create_sample_historical_data(days=30)
    print(f"  Generated {len(historical_data)} days of data")
    print(f"  Date range: {historical_data['date'].min()} to {historical_data['date'].max()}")
    
    # Initialize backtester
    print("\n[STEP 2] Initializing backtester...")
    backtester = OptionsBacktester()
    
    # Run backtest
    print("\n[STEP 3] Running backtest...")
    results = backtester.backtest_strategy(
        strategy_func=iron_condor_backtest_strategy,
        historical_data=historical_data,
        initial_capital=100000
    )
    
    # Display results
    print("\n[STEP 4] Backtest Results:")
    print("=" * 80)
    print(f"  Initial Capital: Rs. {results.get('initial_capital'):,.2f}")
    print(f"  Final Value: Rs. {results.get('final_value'):,.2f}")
    print(f"  Total Return: {results.get('total_return'):.2f}%")
    print(f"  Total Trades: {results.get('total_trades')}")
    print(f"  Win Rate: {results.get('win_rate'):.2f}%")
    print(f"  Max Drawdown: Rs. {results.get('max_drawdown'):,.2f}")
    print(f"  Sharpe Ratio: {results.get('sharpe_ratio'):.2f}")
    
    # Save to Firestore (optional)
    print("\n[STEP 5] Saving results to Firestore...")
    run_id = backtester.save_backtest_results('Iron_Condor_Demo', results)
    
    if run_id:
        print(f"  [OK] Results saved: Iron_Condor_Demo/{run_id}")
    else:
        print("  [INFO] Firestore save skipped (optional)")
    
    print("\n" + "=" * 80)
    print("  BACKTEST COMPLETE")
    print("=" * 80)
    
    if results.get('total_return', 0) > 0:
        print(f"\n  [SUCCESS] Strategy profitable: +{results.get('total_return'):.2f}%")
    else:
        print(f"\n  [INFO] Strategy loss: {results.get('total_return'):.2f}%")
    
    return results

if __name__ == "__main__":
    run_backtest_demo()
