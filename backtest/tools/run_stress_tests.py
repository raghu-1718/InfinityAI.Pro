import subprocess
import sys
import os
import re

CONFIG_PATH = "backtest/config.py"

def read_config():
    with open(CONFIG_PATH, 'r') as f:
        return f.read()

def write_config(content):
    with open(CONFIG_PATH, 'w') as f:
        f.write(content)

def run_backtest_process(data_file="crudeoil_5m_sample.csv"):
    # Run backtest_runner in a subprocess to ensure clean imports
    # We need to modify backtest_runner to accept a data file arg or we modify the calling code
    # The backtest_runner.py has a hardcoded path in __main__. 
    # Let's rely on modifying the runner or just temporarilly swapping the file if strictly needed,
    # BUT backtest_runner.py is code.
    # Better: execute a python command that imports run_backtest and runs it.
    
    cmd = [
        sys.executable, "-c",
        f"from backtest.backtest_runner import run_backtest; from backtest.reporter import generate_report; import os; book = run_backtest(os.path.join('backtest', 'data', '{data_file}')); print('REPORT_JSON_START'); print(generate_report(book)); print('REPORT_JSON_END')"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    
    # Extract report
    output = result.stdout
    if "REPORT_JSON_START" in output:
        report_str = output.split("REPORT_JSON_START")[1].split("REPORT_JSON_END")[0].strip()
        return eval(report_str) # Safe enough for our own internal trusted code
    else:
        print("Error running backtest:", result.stderr)
        return None

def run_stress_suite():
    original_config = read_config()
    results = {}
    
    print("--- 1. Baseline Run ---")
    results['Baseline'] = run_backtest_process()
    
    print("\n--- 2. Stress: Slippage x2 (0.10%) ---")
    # Modify Config
    new_config = original_config.replace("SLIPPAGE_PCT = 0.0005", "SLIPPAGE_PCT = 0.0010")
    write_config(new_config)
    try:
        results['Slippage_x2'] = run_backtest_process()
    finally:
        write_config(original_config) # Restore
        
    print("\n--- 3. Stress: Brokerage x2 (40) ---")
    # Modify Config
    new_config = original_config.replace("BROKERAGE_PER_TRADE = 20", "BROKERAGE_PER_TRADE = 40")
    write_config(new_config)
    try:
        results['Brokerage_x2'] = run_backtest_process()
    finally:
        write_config(original_config) # Restore

    print("\n--- 4. Stress: Volatility Spike ---")
    # Creating data if not exists
    if not os.path.exists("backtest/data/crudeoil_stress_volatility.csv"):
        import backtest.tools.create_stress_data as generator
        generator.create_stress_dataset()
        
    results['Volatility_Spike'] = run_backtest_process("crudeoil_stress_volatility.csv")

    print("\n\n====== STRESS TEST RESULTS ======")
    print(f"{'Scenario':<20} | {'PnL':<10} | {'Trades':<8} | {'Win Rate':<10} | {'Drawdown':<10}")
    print("-" * 70)
    for scenario, res in results.items():
        if res:
            print(f"{scenario:<20} | {res['total_pnl']:<10.2f} | {res['total_trades']:<8} | {res['win_rate']:<10.2f} | {res['max_drawdown']:<10.2f}")
        else:
            print(f"{scenario:<20} | FAILED")

if __name__ == "__main__":
    run_stress_suite()
