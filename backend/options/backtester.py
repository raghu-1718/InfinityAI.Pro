"""
Options Backtesting Framework with Supabase Integration
Replay historical option data and calculate strategy performance
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class OptionsBacktester:
    """
    Backtest options trading strategies with historical data
    """
    
    def __init__(self, db_client=None):
        self.db = db_client
        self.results = []
    
    def fetch_historical_option_data(self, underlying: str, expiry: str, 
                                     start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical option chain snapshots from Supabase
        """
        try:
            if not self.db:
                logger.warning("No database client available for fetching historical data")
                return pd.DataFrame()

            # Fetch from Supabase
            response = self.db.table("option_chain_history").select("*").eq("underlying", underlying).eq("expiry", expiry).gte("date", start_date).lte("date", end_date).execute()
            
            data = response.data if response.data else []
            
            if data:
                df = pd.DataFrame(data)
                logger.info(f"Fetched {len(df)} historical snapshots for {underlying}")
                return df
            else:
                logger.warning(f"No historical data found for {underlying}")
                return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"Error fetching historical option data: {e}")
            return pd.DataFrame()
    
    def backtest_strategy(self, strategy_func, historical_data: pd.DataFrame, 
                         initial_capital: float = 100000) -> Dict[str, Any]:
        """
        Backtest a strategy function on historical data
        
        Args:
            strategy_func: Function that takes (spot, option_chain) and returns trades
            historical_data: DataFrame with historical option snapshots
            initial_capital: Starting capital
        
        Returns:
            Performance metrics dictionary
        """
        try:
            capital = initial_capital
            positions = []
            trades = []
            daily_pnl = []
            
            for idx, row in historical_data.iterrows():
                spot = row.get('spot_price')
                option_chain = row.get('option_chain', [])
                date = row.get('date')
                
                # Get strategy signals
                signal = strategy_func(spot, option_chain)
                
                if signal:
                    # Execute trade
                    trade_cost = signal.get('cost', 0)
                    
                    if capital >= trade_cost:
                        capital -= trade_cost
                        positions.append(signal)
                        trades.append({
                            'date': date,
                            'type': signal.get('type'),
                            'cost': trade_cost,
                            'capital_remaining': capital
                        })
                
                # Calculate current portfolio value
                portfolio_value = capital + sum([pos.get('value', 0) for pos in positions])
                daily_pnl.append({
                    'date': date,
                    'portfolio_value': portfolio_value,
                    'pnl': portfolio_value - initial_capital
                })
            
            # Calculate metrics
            final_value = daily_pnl[-1]['portfolio_value'] if daily_pnl else initial_capital
            total_return = ((final_value - initial_capital) / initial_capital) * 100
            
            # Win rate
            winning_trades = len([t for t in trades if t.get('profit', 0) > 0])
            total_trades = len(trades)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Max drawdown
            pnls = [d['pnl'] for d in daily_pnl]
            cummax = np.maximum.accumulate(pnls)
            drawdown = cummax - pnls
            max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
            
            # Sharpe ratio (simplified)
            returns = np.diff([d['pnl'] for d in daily_pnl])
            sharpe = np.mean(returns) / np.std(returns) if len(returns) > 0 and np.std(returns) > 0 else 0
            
            results = {
                'initial_capital': initial_capital,
                'final_value': round(final_value, 2),
                'total_return': round(total_return, 2),
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(sharpe, 2),
                'trades': trades,
                'daily_pnl': daily_pnl
            }
            
            self.results.append(results)
            return results
        
        except Exception as e:
            logger.error(f"Backtesting error: {e}")
            return {}
    
    def save_backtest_results(self, strategy_name: str, results: Dict[str, Any]):
        """
        Save backtest results to Supabase
        
        Table: backtest_results
        """
        try:
            if not self.db:
                logger.warning("No database client — cannot save backtest results")
                return None

            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.db.table('backtest_results').insert(summary).execute()
            logger.info(f"Saved backtest results: {strategy_name}/{run_id}")
            
            return run_id
        
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")
            return None
    
    def compare_strategies(self, strategy_results: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Compare multiple strategy backtest results
        """
        comparison = []
        
        for result in strategy_results:
            comparison.append({
                'strategy': result.get('strategy_name', 'Unknown'),
                'total_return': result.get('total_return'),
                'win_rate': result.get('win_rate'),
                'sharpe': result.get('sharpe_ratio'),
                'max_dd': result.get('max_drawdown'),
                'trades': result.get('total_trades')
            })
        
        return pd.DataFrame(comparison).sort_values('total_return', ascending=False)


# Demo strategy function
def iron_condor_strategy(spot: float, option_chain: List[Dict]) -> Optional[Dict]:
    """
    Example strategy: Iron Condor when VIX is low
    """
    # Simplified logic
    if len(option_chain) < 4:
        return None
    
    # Check if conditions are met (low volatility, etc.)
    # This would use actual option chain data
    
    return {
        'type': 'Iron Condor',
        'cost': 5000,  # Net premium paid
        'value': 0,  # Current value
        'target_profit': 15000,
        'max_loss': 5000
    }


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  OPTIONS BACKTESTING FRAMEWORK")
    print("=" * 80)
    
    backtester = OptionsBacktester()
    
    print("\n[INFO] Backtesting Framework Features:")
    print("  - Historical option data replay")
    print("  - Strategy P&L calculation")
    print("  - Performance metrics (Return, Win Rate, Sharpe, Max DD)")
    print("  - Supabase integration for results")
    print("  - Strategy comparison")
    
    print("\n[INFO] Supabase Tables:")
    print("  - option_chain_history")
    print("  - backtest_results")
    
    print("\n[INFO] Metrics Calculated:")
    print("  - Total Return (%)")
    print("  - Win Rate (%)")
    print("  - Sharpe Ratio")
    print("  - Maximum Drawdown")
    print("  - Total Trades")
    
    print("\n" + "=" * 80)
    print("  BACKTESTING FRAMEWORK READY")
    print("=" * 80)
