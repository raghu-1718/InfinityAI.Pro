import pandas as pd
import os
from backtest.market_provider import BacktestMarketProvider
from backtest.execution_simulator import SimulatedExecutionEngine
from backtest.metrics import TradeBook
from backtest.engine_bridge import generate_signal, evaluate_signal
from backtest.reporter import generate_report

def run_window_backtest(df_chunk, window_name):
    # Initialize components with DataFrame chunk
    market = BacktestMarketProvider(df_chunk)
    executor = SimulatedExecutionEngine()
    book = TradeBook()

    while market.has_next():
        tick = market.next_tick()
        
        # Engine B (Signal)
        signal = generate_signal(tick)
        
        # Engine A (Risk)
        decision = evaluate_signal(signal)

        # Engine C (Execution)
        if decision["approved"]:
             if decision["side"] in ["BUY", "SELL"]:
                trade = executor.execute(
                    decision["side"],
                    tick["close"],
                    decision["quantity"]
                )
                book.record(trade)
                
    return book

def walk_forward(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: Data file not found at {csv_path}")
        return []
        
    print(f"Loading Real Data: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Ensure Timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    total_rows = len(df)
    print(f"Total Bars: {total_rows}")
    
    # Config
    TRAIN_SIZE = 5000  # Approx 5-6 Days
    TEST_SIZE = 1000   # Approx 1+ Days
    
    start_index = 0
    results = []
    
    print("\n--- Starting Walk-Forward Validation Loop ---")
    print(f"{'Window':<10} | {'Start Time':<20} | {'End Time':<20} | {'Trades':<8} | {'PnL':<10}")
    print("-" * 80)
    
    window_count = 1
    
    while start_index + TRAIN_SIZE + TEST_SIZE <= total_rows:
        # Define Segments
        # Train: [start : start + TRAIN] -> Used for Model Fit (Simulated here)
        # Test:  [start + TRAIN : start + TRAIN + TEST] -> Used for PnL Verification
        
        train_end = start_index + TRAIN_SIZE
        test_end = train_end + TEST_SIZE
        
        train_data = df.iloc[start_index : train_end]
        test_data = df.iloc[train_end : test_end]
        
        # Validation: Strictly no overlap?
        # Actually standard Rolling Window steps forward by TEST_SIZE usually.
        # Or expanding window? 
        # Walk-Forward usually: Train(W), Test(1), Step(1).
        
        # Run Backtest on TEST slice
        book = run_window_backtest(test_data, f"Window-{window_count}")
        report = generate_report(book)
        
        pnl = report['total_pnl']
        trades = report['total_trades']
        
        start_time = test_data.iloc[0]['timestamp']
        end_time = test_data.iloc[-1]['timestamp']
        
        print(f"W-{window_count:<7} | {str(start_time):<20} | {str(end_time):<20} | {trades:<8} | {pnl:<10.2f}")
        
        results.append({
            "window": window_count,
            "start": start_time,
            "end": end_time,
            "pnl": pnl,
            "trades": trades,
            "win_rate": report['win_rate']
        })
        
        # Step forward
        start_index += TEST_SIZE
        window_count += 1

    # Summary
    print("\n=== Walk-Forward Summary ===")
    total_pnl = sum(r['pnl'] for r in results)
    avg_win_rate = sum(r['win_rate'] for r in results) / len(results) if results else 0
    
    print(f"Total Windows: {len(results)}")
    print(f"Cumulative PnL: {total_pnl:.2f}")
    print(f"Avg Win Rate:   {avg_win_rate:.2f}%")
    
    return results

if __name__ == "__main__":
    data_dir = "backtest/data"
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith("_1min_real.csv")]
        
        if not files:
            print("No real data files found in backtest/data/")
        else:
            for f in files:
                print(f"\n{'='*50}")
                print(f"Executing Walk-Forward on: {f}")
                print(f"{'='*50}")
                path = os.path.join(data_dir, f)
                walk_forward(path)
    else:
        print(f"Data directory not found: {data_dir}")
