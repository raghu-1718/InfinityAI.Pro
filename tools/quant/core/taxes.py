"""
SEBI 2026 Statutory Tax & Dhan Brokerage Calculator
"""
from typing import Dict, Any

def calculate_sebi_2026_charges(
    premium_entry: float,
    premium_exit: float,
    lot_size: int,
    lots: int = 1,
    exchange: str = "NSE"
) -> Dict[str, float]:
    """
    Computes exact round-trip brokerage and statutory taxes for NSE/BSE F&O options trades.
    """
    qty = max(1, lot_size * lots)
    buy_turnover = float(premium_entry * qty)
    sell_turnover = float(premium_exit * qty)
    total_turnover = buy_turnover + sell_turnover

    # 1. Brokerage Fees (Flat Rs 20 per executed order for DhanHQ F&O)
    brokerage = 40.0  # Rs 20 Buy + Rs 20 Sell

    # 2. STT (0.125% on sell side premium turnover)
    stt = round(sell_turnover * 0.00125, 2)

    # 3. Exchange Turnover Charges (NSE: 0.0505% on premium turnover)
    exchange_charge_rate = 0.000505 if exchange.upper() == "NSE" else 0.000375
    etc = round(total_turnover * exchange_charge_rate, 2)

    # 4. SEBI Turnover Fee (Rs 10 per Crore = 0.0001%)
    sebi_fee = round(total_turnover * 0.000001, 2)

    # 5. GST (18% on Brokerage + Exchange Charges + SEBI Fees)
    gst = round((brokerage + etc + sebi_fee) * 0.18, 2)

    # 6. Stamp Duty (0.003% on buy side premium turnover)
    stamp_duty = round(buy_turnover * 0.00003, 2)

    total_taxes = round(brokerage + stt + etc + gst + stamp_duty + sebi_fee, 2)
    return {
        "brokerage": brokerage,
        "stt": stt,
        "etc": etc,
        "gst": gst,
        "stamp_duty": stamp_duty,
        "sebi_fee": sebi_fee,
        "total_charges": total_taxes,
        "cost_per_unit": round(total_taxes / qty, 4)
    }
