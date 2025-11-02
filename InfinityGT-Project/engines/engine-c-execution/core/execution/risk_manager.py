from __future__ import annotations

from typing import Dict, List
from .types import RiskCheck, TransactionType, Position


class RiskManager:
    """
    Encapsulates risk rules and scoring.
    Rules are adjustable via constructor. Keeps no state; callers provide
    current positions and daily PnL for evaluation.
    """

    def __init__(self,
                 max_position_size_inr: int = 100_000,
                 max_daily_loss_inr: int = 50_000,
                 max_open_positions: int = 10,
                 leverage_multiplier: int = 5) -> None:
        self.max_position_size = max_position_size_inr
        self.max_daily_loss = max_daily_loss_inr
        self.max_open_positions = max_open_positions
        self.leverage_multiplier = leverage_multiplier

    def assess(self,
               symbol: str,
               quantity: int,
               price: float,
               side: TransactionType,
               positions: Dict[str, Position],
               daily_pnl: float) -> RiskCheck:
        warnings: List[str] = []
        risk_score = 0.0

        # Kill switch is handled by higher layer (OrderManager) if needed

        position_value = quantity * float(price)

        # Position size cap
        if position_value > self.max_position_size:
            warnings.append(
                f"Position size exceeds limit (₹{position_value:,.2f} > ₹{self.max_position_size:,.2f})"
            )
            risk_score += 0.3

        # Daily loss cap
        if daily_pnl < -self.max_daily_loss:
            warnings.append(f"Daily loss limit exceeded (₹{daily_pnl:,.2f})")
            risk_score += 0.5

        # Open positions cap
        if len(positions) >= self.max_open_positions:
            warnings.append(f"Maximum open positions reached ({len(positions)})")
            risk_score += 0.2

        # Exposure calculation
        current_exposure = sum(
            p.quantity * float(p.current_price or 0.0) for p in positions.values()
        )
        total_exposure = current_exposure + position_value
        max_total_exposure = self.max_position_size * self.leverage_multiplier
        if total_exposure > max_total_exposure:
            warnings.append("Total exposure limit exceeded")
            risk_score += 0.4

        passed = (risk_score < 0.7) and (len(warnings) == 0)

        return RiskCheck(
            passed=passed,
            risk_score=risk_score,
            warnings=warnings,
            max_position_size=self.max_position_size,
            current_exposure=current_exposure,
        )
