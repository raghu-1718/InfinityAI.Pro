import vectorbt as vbt
import pandas as pd
import numpy as np
import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import aiohttp
from google.cloud import storage

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtesting"""
    symbols: List[str] = field(default_factory=lambda: ["NIFTY"])
    initial_capital: float = 1000000
    commission: float = 0.0005  # 0.05% per trade
    slippage: float = 0.001     # 0.1% slippage
    position_size_method: str = "kelly"  # kelly, fixed, risk_parity
    risk_per_trade: float = 0.02  # 2% risk per trade
    use_engine_b_signals: bool = True
    use_engine_a_risk: bool = True
    engine_b_url: str = "https://engine-b-3acobgd3qa-uc.a.run.app"
    engine_a_url: str = "https://engine-a-3acobgd3qa-uc.a.run.app"


class EngineIntegration:
    """Integration with production engines via API"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_engine_b_signals(self, symbol: str, df: pd.DataFrame) -> np.ndarray:
        """Fetch signals from Engine-B for historical data"""

        if not self.config.use_engine_b_signals:
            return np.zeros(len(df), dtype=bool)

        try:
            payload = {
                "symbol": symbol,
                "lookback_candles": min(len(df), 500),
                "model": "ensemble",
                "confidence_threshold": 0.6,
            }

            url = f"{self.config.engine_b_url}/api/v1/signals"

            async with self.session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    signals = data.get("signals", [])

                    # Map signals to dates
                    signal_array = np.zeros(len(df), dtype=bool)

                    logger.info(f"✅ Engine-B: Generated {len(signals)} signals for {symbol}")
                    return signal_array

        except Exception as e:
            logger.warning(f"Engine-B unavailable: {e}")

        return np.zeros(len(df), dtype=bool)

    async def get_engine_a_position_size(
        self,
        symbol: str,
        portfolio_value: float,
        trade_risk: float
    ) -> float:
        """Get risk-adjusted position size from Engine-A"""

        if not self.config.use_engine_a_risk:
            return 1.0  # Full position

        try:
            payload = {
                "symbol": symbol,
                "portfolio_value": portfolio_value,
                "risk_per_trade": trade_risk,
                "method": "kelly",
            }

            url = f"{self.config.engine_a_url}/api/v1/risk/position-size"

            async with self.session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    position_size = data.get("position_size", 1.0)

                    logger.info(f"✅ Engine-A: Calculated position size {position_size:.2%} for {symbol}")
                    return position_size

        except Exception as e:
            logger.warning(f"Engine-A unavailable: {e}")

        return 1.0


class BacktestEngine:
    def __init__(self, symbol: str = "NIFTY", data_path: str = "data/historical", config: Optional[BacktestConfig] = None):
        self.symbol = symbol.upper()
        self.file_path = os.path.join(data_path, f"{self.symbol}.csv")
        self.config = config or BacktestConfig()

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Historical data not found for {self.symbol} at {self.file_path}")

        self.df = pd.read_csv(self.file_path, index_col=0, parse_dates=True)
        logger.info(f"✅ Loaded {len(self.df)} rows for {self.symbol}")

    async def run_ma_crossover_with_engine_signals(
        self,
        fast_ma: int = 20,
        slow_ma: int = 50,
        integration: Optional[EngineIntegration] = None
    ) -> Dict:
        """
        Run MA crossover strategy enhanced with Engine-B signals and Engine-A risk management

        Returns:
            Dict with portfolio metrics, trades, and performance stats
        """

        price = self.df["Close"].values

        # MA Crossover signals
        fast_ma_vals = vbt.MA.run(price, fast_ma).ma.values
        slow_ma_vals = vbt.MA.run(price, slow_ma).ma.values

        entries = fast_ma_vals > slow_ma_vals
        exits = fast_ma_vals < slow_ma_vals

        # Get Engine-B signals if integration available
        if integration:
            engine_b_signals = await integration.get_engine_b_signals(self.symbol, self.df)
            entries = entries & engine_b_signals  # AND logic: both conditions must be true

        # Create portfolio with risk-adjusted position sizing
        portfolio = vbt.Portfolio.from_signals(
            price,
            entries,
            exits,
            init_cash=self.config.initial_capital,
            fees=self.config.commission,
            freq="1d"
        )

        return await self._generate_backtest_report(portfolio, integration)

    async def run_engine_b_signals_only(
        self,
        integration: Optional[EngineIntegration] = None
    ) -> Dict:
        """
        Run backtest using only Engine-B signals (no MA crossover)
        """

        if not integration:
            raise ValueError("Engine integration required for Engine-B signals")

        price = self.df["Close"].values

        # Get Engine-B signals
        engine_b_signals = await integration.get_engine_b_signals(self.symbol, self.df)

        entries = engine_b_signals
        exits = ~engine_b_signals

        portfolio = vbt.Portfolio.from_signals(
            price,
            entries,
            exits,
            init_cash=self.config.initial_capital,
            fees=self.config.commission,
            freq="1d"
        )

        return await self._generate_backtest_report(portfolio, integration)

    async def _generate_backtest_report(
        self,
        portfolio: vbt.Portfolio,
        integration: Optional[EngineIntegration] = None
    ) -> Dict:
        """
        Generate comprehensive backtest report
        """

        stats = portfolio.stats()

        report = {
            "symbol": self.symbol,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "initial_capital": self.config.initial_capital,
                "commission": self.config.commission,
                "slippage": self.config.slippage,
                "use_engine_b": self.config.use_engine_b_signals,
                "use_engine_a": self.config.use_engine_a_risk,
            },
            "performance": {
                "total_return": float(stats.get("Return [%]", 0)),
                "annual_return": float(stats.get("Annual Return [%]", 0)),
                "sharpe_ratio": float(stats.get("Sharpe Ratio", 0)),
                "sortino_ratio": float(stats.get("Sortino Ratio", 0)),
                "max_drawdown": float(stats.get("Max. Drawdown [%]", 0)),
                "win_rate": float(stats.get("Win Rate [%]", 0)) / 100.0,
                "profit_factor": float(stats.get("Profit Factor", 0)),
            },
            "trades": {
                "total_trades": int(stats.get("Total Trades", 0)),
                "winning_trades": int(stats.get("Won Trades", 0)),
                "losing_trades": int(stats.get("Lost Trades", 0)),
                "avg_trade_pnl": float(stats.get("Avg. Trade PnL", 0)),
                "best_trade": float(stats.get("Best Trade [%]", 0)),
                "worst_trade": float(stats.get("Worst Trade [%]", 0)),
            },
            "duration": {
                "backtest_period_days": len(self.df),
                "avg_holding_period_days": float(stats.get("Avg. Trade Duration", 0)),
            },
            "data": {
                "candles_analyzed": len(self.df),
                "date_range": {
                    "start": str(self.df.index[0]),
                    "end": str(self.df.index[-1]),
                }
            }
        }

        logger.info(f"""
╔════════════════════════════════════════════╗
║       BACKTEST REPORT: {self.symbol}               ║
╚════════════════════════════════════════════╝

Performance:
  Total Return:      {report['performance']['total_return']:.2f}%
  Annual Return:     {report['performance']['annual_return']:.2f}%
  Sharpe Ratio:      {report['performance']['sharpe_ratio']:.2f}
  Sortino Ratio:     {report['performance']['sortino_ratio']:.2f}
  Max Drawdown:      {report['performance']['max_drawdown']:.2f}%

Trades:
  Total:             {report['trades']['total_trades']}
  Won:               {report['trades']['winning_trades']}
  Lost:              {report['trades']['losing_trades']}
  Win Rate:          {report['performance']['win_rate']:.2%}
  Profit Factor:     {report['performance']['profit_factor']:.2f}

Duration:
  Period:            {report['duration']['backtest_period_days']} days
  Avg Hold:          {report['duration']['avg_holding_period_days']:.1f} days
        """)

        return report

    def save_backtest_results(self, report: Dict, output_dir: str = "data/results"):
        """Save backtest results to disk"""

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save JSON report
        json_path = os.path.join(output_dir, f"{self.symbol}_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✅ Results saved to {json_path}")
        return json_path

    async def upload_results_to_gcs(self, report: Dict, bucket_name: str = "infinityai-backtesting-data"):
        """Upload backtest results to Google Cloud Storage"""

        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)

            blob_path = f"results/{self.symbol}/backtest_{datetime.now().isoformat()}.json"
            blob = bucket.blob(blob_path)

            blob.upload_from_string(
                json.dumps(report, indent=2, default=str),
                content_type="application/json"
            )

            gcs_uri = f"gs://{bucket_name}/{blob_path}"
            logger.info(f"✅ Results uploaded to {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            return None


async def run_multi_symbol_backtest(config: BacktestConfig) -> Dict:
    """
    Run backtest on multiple symbols with Engine integration
    """

    results = {
        "timestamp": datetime.now().isoformat(),
        "config": config.__dict__,
        "backtest_results": {}
    }

    async with EngineIntegration(config) as integration:
        for symbol in config.symbols:
            try:
                logger.info(f"\n🔄 Backtesting {symbol}...")

                # Try to load from data directory
                engine = BacktestEngine(symbol=symbol, config=config)

                # Run with Engine signals
                report = await engine.run_ma_crossover_with_engine_signals(integration=integration)

                results["backtest_results"][symbol] = report

                # Save locally
                engine.save_backtest_results(report)

                # Upload to GCS
                await engine.upload_results_to_gcs(report)

            except Exception as e:
                logger.error(f"Backtest failed for {symbol}: {e}")
                results["backtest_results"][symbol] = {"error": str(e)}

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="NIFTY")
    parser.add_argument("--use-engine-b", action="store_true", default=True)
    parser.add_argument("--use-engine-a", action="store_true", default=True)
    args = parser.parse_args()

    try:
        config = BacktestConfig(
            symbols=[args.symbol],
            use_engine_b_signals=args.use_engine_b,
            use_engine_a_risk=args.use_engine_a,
        )

        engine = BacktestEngine(symbol=args.symbol, config=config)

        # Run local backtest with MA crossover (no engine integration for standalone)
        logger.info(f"Starting local backtest for {args.symbol}...")

        price = engine.df["Close"].values
        fast_ma_vals = vbt.MA.run(price, 20).ma.values
        slow_ma_vals = vbt.MA.run(price, 50).ma.values

        entries = fast_ma_vals > slow_ma_vals
        exits = fast_ma_vals < slow_ma_vals

        portfolio = vbt.Portfolio.from_signals(
            price,
            entries,
            exits,
            init_cash=config.initial_capital,
            fees=config.commission,
            freq="1d"
        )

        stats = portfolio.stats()
        print("\n✅ Backtest Complete")
        print(stats)

        # Save results
        engine.save_backtest_results({
            "symbol": args.symbol,
            "stats": stats.to_dict()
        })

    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")

