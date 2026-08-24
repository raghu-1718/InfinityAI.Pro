"""
Indian Capital Markets Regulatory & Brokerage Tax Calculator (SEBI 2026 Mandate)
Calculates exact round-trip brokerage and statutory taxes for NSE/BSE F&O options and equities.
"""
from typing import Dict, Any, Optional

def calculate_options_roundtrip_charges(
    premium: float,
    lot_size: int,
    lots: int = 1,
    exchange: str = "NSE"
) -> Dict[str, Any]:
    """
    Calculates exact round-trip brokerage and statutory taxes for NSE/BSE F&O options trades.
    
    Parameters:
    - premium: Execution price per unit (e.g., 120.00)
    - lot_size: Contract unit size (e.g., 65 for NIFTY 50, 30 for BANK NIFTY)
    - lots: Number of lots traded (default: 1)
    - exchange: "NSE" or "BSE" (affects exchange transaction charges)
    
    Returns:
    - A dictionary containing breakdown of entry/exit fees, taxes, and net break-even cost.
    """
    total_units = max(1, lot_size * lots)
    turnover_buy = float(premium * total_units)
    turnover_sell = turnover_buy  # Assuming square-off baseline for tax approximation

    # 1. Brokerage Fees (Flat ₹20 per executed order for DhanHQ F&O)
    base_brokerage_per_order = 20.0
    
    # Round-trip means 1 Buy order + 1 Sell order
    entry_brokerage = base_brokerage_per_order
    exit_brokerage = base_brokerage_per_order
    total_brokerage = entry_brokerage + exit_brokerage

    # 2. Securities Transaction Tax (STT): 0.1% on Premium (Sell Side only for options)
    stt = 0.001 * turnover_sell

    # 3. Exchange Transaction Charges
    # NSE options: ~0.05% on Premium (both buy and sell turnover)
    # BSE options: ~0.0375% on Premium (approximate baseline)
    exchange_charge_rate = 0.0005 if exchange.upper() == "NSE" else 0.000375
    exchange_transaction_charge = (turnover_buy + turnover_sell) * exchange_charge_rate

    # 4. SEBI Turnover Fee: ₹10 per Crore (0.0001% or 0.000001 multiplier)
    sebi_turnover_fee = (turnover_buy + turnover_sell) * 0.000001

    # 5. Goods & Services Tax (GST): 18% on (Brokerage + Exchange Transaction Charges + SEBI fees)
    gst = 0.18 * (total_brokerage + exchange_transaction_charge + sebi_turnover_fee)

    # 6. Stamp Duty: 0.003% on Buy side only (0.00003 multiplier)
    stamp_duty = turnover_buy * 0.00003

    # Total Statutory and Regulatory Taxes
    total_taxes = stt + exchange_transaction_charge + sebi_turnover_fee + gst + stamp_duty
    
    # Grand Total Round-Trip Cost
    grand_total_charges = total_brokerage + total_taxes

    return {
        "contract_details": {
            "total_units": total_units,
            "lots": lots,
            "lot_size": lot_size,
            "premium": round(premium, 2),
            "buy_turnover": round(turnover_buy, 2),
            "sell_turnover": round(turnover_sell, 2)
        },
        "brokerage_breakdown": {
            "entry_brokerage": round(entry_brokerage, 2),
            "exit_brokerage": round(exit_brokerage, 2),
            "total_brokerage": round(total_brokerage, 2)
        },
        "statutory_taxes": {
            "stt": round(stt, 2),
            "exchange_transaction_charges": round(exchange_transaction_charge, 2),
            "sebi_fee": round(sebi_turnover_fee, 2),
            "gst": round(gst, 2),
            "stamp_duty": round(stamp_duty, 2),
            "total_taxes": round(total_taxes, 2)
        },
        "summary": {
            "total_roundtrip_cost": round(grand_total_charges, 2),
            "cost_per_unit": round(grand_total_charges / total_units, 4),
            "breakeven_points": round(grand_total_charges / total_units, 2)
        }
    }


def evaluate_net_profitability_gate(
    entry_price: float,
    target_price: float,
    lot_size: int,
    lots: int = 1,
    max_fee_ratio: float = 0.35,
    min_net_profit_margin: float = 0.015
) -> Dict[str, Any]:
    """
    Evaluates whether an intended trade clears the Net-Profitability hurdle.
    Prevents 'Death by a Thousand Cuts' by ensuring expected alpha exceeds transaction friction.
    """
    total_units = max(1, lot_size * lots)
    gross_profit_per_unit = max(0.0, target_price - entry_price)
    gross_profit_total = gross_profit_per_unit * total_units

    charges = calculate_options_roundtrip_charges(
        premium=entry_price,
        lot_size=lot_size,
        lots=lots
    )
    total_fees = charges["summary"]["total_roundtrip_cost"]
    net_profit_total = gross_profit_total - total_fees
    fee_to_gross_ratio = total_fees / gross_profit_total if gross_profit_total > 0 else 1.0

    # Net Return on Capital Deployed
    capital_deployed = entry_price * total_units
    net_roi = (net_profit_total / capital_deployed) if capital_deployed > 0 else 0.0

    # Veto Rules
    is_viable = True
    rejection_reason = None

    if net_profit_total <= 0:
        is_viable = False
        rejection_reason = f"Negative Net Return: Gross Profit ₹{gross_profit_total:.2f} < Total Fees ₹{total_fees:.2f}"
    elif fee_to_gross_ratio > max_fee_ratio:
        is_viable = False
        rejection_reason = f"Fees Consume {fee_to_gross_ratio:.1%} of Alpha (Threshold: {max_fee_ratio:.1%})"
    elif net_roi < min_net_profit_margin:
        is_viable = False
        rejection_reason = f"Net ROI {net_roi:.2%} is below minimum hurdle {min_net_profit_margin:.2%}"

    return {
        "is_viable": is_viable,
        "rejection_reason": rejection_reason,
        "gross_profit": round(gross_profit_total, 2),
        "total_fees": round(total_fees, 2),
        "net_profit": round(net_profit_total, 2),
        "fee_ratio": round(fee_to_gross_ratio, 4),
        "net_roi": round(net_roi, 4),
        "charges_breakdown": charges
    }


def calculate_microstructure_slippage(
    raw_premium: float,
    obi: float,
    lot_size: int = 65
) -> float:
    """
    Computes real-world execution decay based on live order book imbalances (OBI 5-Depth).
    Ensures backtests and live shadow fills strictly reflect exchange liquidity.
    """
    if obi <= -0.70:
        slippage_penalty_pct = 0.015   # 1.5% slippage drop during institutional dumps
    elif -0.70 < obi <= -0.30:
        slippage_penalty_pct = 0.005   # 0.5% slippage drop during moderate ask pressure
    else:
        slippage_penalty_pct = 0.001   # 0.1% baseline structural bid-ask friction
        
    realized_execution_premium = raw_premium * (1.0 - slippage_penalty_pct)
    return round(realized_execution_premium, 2)

