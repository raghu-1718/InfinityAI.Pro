"""
Automated Verification Script for 6-Month Backtesting Engine
Tests MA Crossover, RSI Reversion, MACD Momentum, and Bollinger Bands strategies.
"""
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'engine-c'))
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def run_backtest_tests():
    print("=" * 80)
    print("6-MONTH QUANTITATIVE BACKTESTING ENGINE VERIFICATION")
    print("=" * 80)

    strategies = ["MA_CROSSOVER", "RSI_REVERSION", "MACD_MOMENTUM", "BOLLINGER_BANDS"]

    for strat in strategies:
        print(f"\nRunning 6-Month Backtest for Strategy: {strat}...")
        payload = {
            "user_id": "local-user-123",
            "security_id": "13",
            "exchange_segment": "IDX_I",
            "instrument_type": "INDEX",
            "strategy_name": strat,
            "months": 6,
            "initial_capital": 1000000.0,
            "position_size_pct": 0.2,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.04
        }

        res = client.post("/api/dhan/v2/backtest", json=payload)
        print(f"  - Status Code: {res.status_code}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json().get("data", {})
        print(f"  - Period: {data.get('period')}")
        print(f"  - Initial Capital: ₹{data.get('initial_capital'):,.2f}")
        print(f"  - Final Capital: ₹{data.get('final_capital'):,.2f}")
        print(f"  - Total PnL: ₹{data.get('total_pnl'):,.2f} ({data.get('total_return_pct')}%)")
        print(f"  - Total Trades: {data.get('total_trades')} (Wins: {data.get('winning_trades')}, Losses: {data.get('losing_trades')})")
        print(f"  - Win Rate: {data.get('win_rate_pct')}%")
        print(f"  - Profit Factor: {data.get('profit_factor')}")
        print(f"  - Max Drawdown: {data.get('max_drawdown_pct')}%")
        print(f"  - Sharpe Ratio: {data.get('sharpe_ratio')}")
        print(f"  - Equity Curve Points: {len(data.get('equity_curve', []))}")
        
        assert data.get("initial_capital") == 1000000.0
        assert "equity_curve" in data
        assert len(data.get("equity_curve", [])) > 0
        print(f"  ✅ 6-Month Backtest for {strat} PASSED")

    print("\n" + "=" * 80)
    print("ALL 6-MONTH BACKTESTING VERIFICATION TESTS PASSED SUCCESSFULLY 🎉")
    print("=" * 80)

if __name__ == "__main__":
    run_backtest_tests()
