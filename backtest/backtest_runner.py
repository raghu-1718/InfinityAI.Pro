from backtest.market_provider import BacktestMarketProvider
from backtest.execution_simulator import SimulatedExecutionEngine
from backtest.metrics import TradeBook
# Using the bridge adapter to connect to real engines (or fall back to simulation)
from backtest.engine_bridge import generate_signal, evaluate_signal
from backtest.reporter import generate_report

def run_backtest(csv_path):
    print(f"Starting Backtest on {csv_path}...")
    market = BacktestMarketProvider(csv_path)
    executor = SimulatedExecutionEngine()
    book = TradeBook()

    while market.has_next():
        tick = market.next_tick()

        # Phase 1: Signal Generation (Engine B)
        # In a real system, this calls the AI model
        signal = generate_signal(tick)
        
        # Phase 2: Risk Evaluation (Engine A)
        # In a real system, this checks portfolio risk limits
        decision = evaluate_signal(signal)

        # Phase 3: Execution (Engine C Simulator)
        if decision["approved"]:
            if decision["side"] in ["BUY", "SELL"]:
                trade = executor.execute(
                    decision["side"],
                    tick["close"],
                    decision["quantity"]
                )
                book.record(trade)
    
    print("Backtest Complete.")
    return book

if __name__ == "__main__":
    # Example usage
    import os
    # Use absolute path for reliability
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "data", "crudeoil_5m_sample.csv")
    
    if os.path.exists(data_path):
        trade_book = run_backtest(data_path)
        report = generate_report(trade_book)
        print("\n=== Backtest Report ===")
        print(report)
    else:
        print(f"Error: Data file not found at {data_path}")
