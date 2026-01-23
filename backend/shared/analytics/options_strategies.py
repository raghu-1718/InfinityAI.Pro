"""
Options Trading Strategies
Implements multi-leg options strategies (Iron Condor, Spreads, Covered Call)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Options strategy types"""
    IRON_CONDOR = "iron_condor"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    COVERED_CALL = "covered_call"
    STRADDLE = "straddle"
    STRANGLE = "strangle"


class OptionsStrategy:
    """
    Base class for multi-leg options strategies.
    Provides P&L calculation, Greeks aggregation, and risk metrics.
    """

    def __init__(
        self,
        symbol: str,
        spot_price: float,
        expiry: str,
        volatility: float = 0.18
    ):
        self.symbol = symbol
        self.spot_price = spot_price
        self.expiry = expiry
        self.volatility = volatility
        self.legs: List[Dict[str, Any]] = []

    def add_leg(
        self,
        strike: float,
        option_type: str,  # "CE" or "PE"
        quantity: int,  # Positive for buy, negative for sell
        premium: float
    ):
        """Add a leg to the strategy"""
        self.legs.append({
            "strike": strike,
            "option_type": option_type,
            "quantity": quantity,
            "premium": premium
        })

    def calculate_pnl(self, spot_at_expiry: float) -> float:
        """
        Calculate P&L at a given spot price at expiry.

        Returns:
            Total P&L for the strategy
        """
        total_pnl = 0

        for leg in self.legs:
            strike = leg["strike"]
            option_type = leg["option_type"]
            quantity = leg["quantity"]
            premium = leg["premium"]

            # Calculate intrinsic value at expiry
            if option_type == "CE":
                intrinsic = max(0, spot_at_expiry - strike)
            else:  # PE
                intrinsic = max(0, strike - spot_at_expiry)

            # P&L = (Intrinsic value - Premium paid) × Quantity
            # For sold options (negative quantity), we collect premium
            if quantity > 0:  # Bought
                leg_pnl = (intrinsic - premium) * quantity
            else:  # Sold
                leg_pnl = (premium - intrinsic) * abs(quantity)

            total_pnl += leg_pnl

        return round(total_pnl, 2)

    def calculate_pnl_range(
        self,
        min_price: float,
        max_price: float,
        steps: int = 50
    ) -> List[Dict[str, float]]:
        """
        Calculate P&L across a range of spot prices.

        Returns:
            List of {"spot": price, "pnl": pnl_value}
        """
        price_range = []
        step_size = (max_price - min_price) / steps

        for i in range(steps + 1):
            spot = min_price + i * step_size
            pnl = self.calculate_pnl(spot)
            price_range.append({
                "spot": round(spot, 2),
                "pnl": pnl
            })

        return price_range

    def max_profit(self, price_range: List[float]) -> float:
        """Calculate maximum profit from P&L range"""
        return max(self.calculate_pnl(p) for p in price_range)

    def max_loss(self, price_range: List[float]) -> float:
        """Calculate maximum loss from P&L range"""
        return min(self.calculate_pnl(p) for p in price_range)

    def breakeven_points(
        self,
        min_price: float,
        max_price: float,
        tolerance: float = 1.0
    ) -> List[float]:
        """Find breakeven points where P&L = 0"""
        breakevens = []
        pnl_data = self.calculate_pnl_range(min_price, max_price, steps=100)

        for i in range(len(pnl_data) - 1):
            # Check for sign change (crossing zero)
            if pnl_data[i]["pnl"] * pnl_data[i + 1]["pnl"] < 0:
                # Approximate breakeven
                breakeven = (pnl_data[i]["spot"] + pnl_data[i + 1]["spot"]) / 2
                breakevens.append(round(breakeven, 2))

        return breakevens


class IronCondorStrategy(OptionsStrategy):
    """
    Iron Condor: 4-leg neutral strategy.

    Structure:
    - Sell OTM Call (higher strike)
    - Buy farther OTM Call (hedge)
    - Sell OTM Put (lower strike)
    - Buy farther OTM Put (hedge)

    Profit zone: Stock stays between short strikes
    Max profit: Net premium collected
    Max loss: Strike width - Net premium
    """

    def __init__(
        self,
        symbol: str,
        spot_price: float,
        expiry: str,
        call_short_strike: float,
        call_long_strike: float,
        put_short_strike: float,
        put_long_strike: float,
        lot_size: int = 50,
        volatility: float = 0.18
    ):
        super().__init__(symbol, spot_price, expiry, volatility)

        # Validate strikes
        assert put_long_strike < put_short_strike < spot_price < call_short_strike < call_long_strike, \
            "Invalid strike order for Iron Condor"

        self.lot_size = lot_size

        # Calculate rough premiums (would come from market data in production)
        # These are placeholder values
        call_short_premium = self._estimate_premium(call_short_strike, "CE")
        call_long_premium = self._estimate_premium(call_long_strike, "CE")
        put_short_premium = self._estimate_premium(put_short_strike, "PE")
        put_long_premium = self._estimate_premium(put_long_strike, "PE")

        # Build legs
        self.add_leg(call_short_strike, "CE", -lot_size, call_short_premium)  # Sell
        self.add_leg(call_long_strike, "CE", lot_size, call_long_premium)     # Buy
        self.add_leg(put_short_strike, "PE", -lot_size, put_short_premium)    # Sell
        self.add_leg(put_long_strike, "PE", lot_size, put_long_premium)       # Buy

        # Calculate metrics
        self.net_credit = (call_short_premium - call_long_premium +
                           put_short_premium - put_long_premium) * lot_size
        self.call_spread_width = call_long_strike - call_short_strike
        self.put_spread_width = put_short_strike - put_long_strike
        self.max_profit = self.net_credit
        self.max_loss = max(self.call_spread_width, self.put_spread_width) * lot_size - self.net_credit

    def _estimate_premium(self, strike: float, option_type: str) -> float:
        """Rough premium estimation (would use Black-Scholes in production)"""
        from shared.analytics.greeks_calculator import BlackScholesGreeks

        days_to_expiry = (datetime.strptime(self.expiry, "%Y-%m-%d") - datetime.now()).days
        time_to_expiry = days_to_expiry / 365.0

        return BlackScholesGreeks.calculate_option_price(
            spot=self.spot_price,
            strike=strike,
            time_to_expiry=time_to_expiry,
            volatility=self.volatility,
            option_type=option_type
        )

    def summary(self) -> Dict[str, Any]:
        """Get strategy summary"""
        return {
            "strategy": "Iron Condor",
            "symbol": self.symbol,
            "spot_price": self.spot_price,
            "expiry": self.expiry,
            "lot_size": self.lot_size,
            "legs": len(self.legs),
            "net_credit": round(self.net_credit, 2),
            "max_profit": round(self.max_profit, 2),
            "max_loss": round(self.max_loss, 2),
            "breakeven_lower": self.legs[2]["strike"] - self.net_credit / self.lot_size,
            "breakeven_upper": self.legs[0]["strike"] + self.net_credit / self.lot_size,
            "risk_reward_ratio": abs(self.max_loss / self.max_profit) if self.max_profit > 0 else 0
        }


class BullCallSpreadStrategy(OptionsStrategy):
    """
    Bull Call Spread: 2-leg bullish strategy.

    Structure:
    - Buy Call at lower strike
    - Sell Call at higher strike

    Profit zone: Stock rises above lower strike
    Max profit: Strike width - Net debit
    Max loss: Net debit (premium paid)
    """

    def __init__(
        self,
        symbol: str,
        spot_price: float,
        expiry: str,
        long_strike: float,
        short_strike: float,
        lot_size: int = 50,
        volatility: float = 0.18
    ):
        super().__init__(symbol, spot_price, expiry, volatility)

        assert long_strike < short_strike, "Long strike must be lower than short strike"

        self.lot_size = lot_size

        # Estimate premiums
        long_premium = self._estimate_premium(long_strike, "CE")
        short_premium = self._estimate_premium(short_strike, "CE")

        # Build legs
        self.add_leg(long_strike, "CE", lot_size, long_premium)   # Buy
        self.add_leg(short_strike, "CE", -lot_size, short_premium)  # Sell

        # Calculate metrics
        self.net_debit = (long_premium - short_premium) * lot_size
        self.spread_width = short_strike - long_strike
        self.max_profit = (self.spread_width * lot_size) - self.net_debit
        self.max_loss = self.net_debit

    def _estimate_premium(self, strike: float, option_type: str) -> float:
        """Rough premium estimation"""
        from shared.analytics.greeks_calculator import BlackScholesGreeks

        days_to_expiry = (datetime.strptime(self.expiry, "%Y-%m-%d") - datetime.now()).days
        time_to_expiry = days_to_expiry / 365.0

        return BlackScholesGreeks.calculate_option_price(
            spot=self.spot_price,
            strike=strike,
            time_to_expiry=time_to_expiry,
            volatility=self.volatility,
            option_type=option_type
        )

    def summary(self) -> Dict[str, Any]:
        """Get strategy summary"""
        return {
            "strategy": "Bull Call Spread",
            "symbol": self.symbol,
            "spot_price": self.spot_price,
            "expiry": self.expiry,
            "lot_size": self.lot_size,
            "legs": len(self.legs),
            "net_debit": round(self.net_debit, 2),
            "max_profit": round(self.max_profit, 2),
            "max_loss": round(self.max_loss, 2),
            "breakeven": self.legs[0]["strike"] + self.net_debit / self.lot_size,
            "risk_reward_ratio": abs(self.max_loss / self.max_profit) if self.max_profit > 0 else 0
        }


class CoveredCallStrategy(OptionsStrategy):
    """
    Covered Call: Income generation strategy.

    Structure:
    - Own 100 shares of stock
    - Sell 1 Call option (OTM)

    Profit zone: Stock stays below strike (collect premium)
    Max profit: Premium + (Strike - Purchase price) if assigned
    Max loss: Unlimited (stock can go to zero)
    """

    def __init__(
        self,
        symbol: str,
        spot_price: float,
        purchase_price: float,
        expiry: str,
        call_strike: float,
        shares: int = 100,
        volatility: float = 0.18
    ):
        super().__init__(symbol, spot_price, expiry, volatility)

        self.purchase_price = purchase_price
        self.shares = shares

        # Estimate call premium
        call_premium = self._estimate_premium(call_strike, "CE")

        # Build leg (just the sold call, stock is already owned)
        self.add_leg(call_strike, "CE", -shares, call_premium)

        # Calculate metrics
        self.premium_income = call_premium * shares
        self.stock_gain_if_assigned = (call_strike - purchase_price) * shares
        self.max_profit = self.premium_income + self.stock_gain_if_assigned

    def _estimate_premium(self, strike: float, option_type: str) -> float:
        """Rough premium estimation"""
        from shared.analytics.greeks_calculator import BlackScholesGreeks

        days_to_expiry = (datetime.strptime(self.expiry, "%Y-%m-%d") - datetime.now()).days
        time_to_expiry = days_to_expiry / 365.0

        return BlackScholesGreeks.calculate_option_price(
            spot=self.spot_price,
            strike=strike,
            time_to_expiry=time_to_expiry,
            volatility=self.volatility,
            option_type=option_type
        )

    def summary(self) -> Dict[str, Any]:
        """Get strategy summary"""
        return {
            "strategy": "Covered Call",
            "symbol": self.symbol,
            "spot_price": self.spot_price,
            "purchase_price": self.purchase_price,
            "expiry": self.expiry,
            "shares": self.shares,
            "legs": len(self.legs),
            "premium_income": round(self.premium_income, 2),
            "max_profit": round(self.max_profit, 2),
            "return_if_assigned": round((self.max_profit / (self.purchase_price * self.shares)) * 100, 2)
        }


# Factory function for creating strategies
def create_strategy(
    strategy_type: str,
    **kwargs
) -> OptionsStrategy:
    """
    Factory function to create options strategies.

    Example:
        >>> strategy = create_strategy(
                "iron_condor",
                symbol="NIFTY",
                spot_price=21000,
                expiry="2024-01-25",
                call_short_strike=21500,
                call_long_strike=21600,
                put_short_strike=20500,
                put_long_strike=20400
            )
    """
    strategies = {
        "iron_condor": IronCondorStrategy,
        "bull_call_spread": BullCallSpreadStrategy,
        "covered_call": CoveredCallStrategy
    }

    strategy_class = strategies.get(strategy_type)
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_type}")

    return strategy_class(**kwargs)
