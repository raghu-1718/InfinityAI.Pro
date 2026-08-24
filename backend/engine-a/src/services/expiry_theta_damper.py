"""
InfinityAI.Pro — Expiry Afternoon Theta Damper & Dynamic Holiday Shift Engine
=============================================================================
Protects Option Buyers against non-linear late-afternoon Theta decay on weekly
and monthly expiry days by dynamically adapting take-profit targets and trailing stops.

Accounts for 2026 SEBI Mandates & Mid-Week Indian Market Holiday Expiry Shifts:
  • NSE (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY): Target Tuesday (1) -> Shifts to Monday (0) on holidays.
  • BSE (SENSEX, BANKEX): Target Thursday (3) -> Shifts to Wednesday (2) on holidays.
  • MCX (CRUDEOIL): Target Friday (4) -> Shifts to Thursday (3) on holidays.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Set

logger = logging.getLogger("InfinityAI.ExpiryThetaDamper")

# Official 2026 NSE/BSE Trading Holidays (YYYY-MM-DD)
DEFAULT_NSE_BSE_HOLIDAYS_2026: Set[str] = {
    "2026-01-26",  # Republic Day (Mon)
    "2026-03-03",  # Holi (Tue - NSE Expiry Shifts to Mon 2026-03-02)
    "2026-03-26",  # Ram Navami (Thu - BSE Expiry Shifts to Wed 2026-03-25)
    "2026-03-31",  # Mahavir Jayanti (Tue - NSE Expiry Shifts to Mon 2026-03-30)
    "2026-04-03",  # Good Friday (Fri)
    "2026-04-14",  # Dr. Ambedkar Jayanti (Tue - NSE Expiry Shifts to Mon 2026-04-13)
    "2026-05-01",  # Maharashtra Day (Fri)
    "2026-05-28",  # Bakri Id / Eid-ul-Adha (Thu - BSE Expiry Shifts to Wed 2026-05-27)
    "2026-06-26",  # Muharram (Fri)
    "2026-09-14",  # Ganesh Chaturthi (Mon)
    "2026-10-02",  # Mahatma Gandhi Jayanti (Fri)
    "2026-10-20",  # Dussehra (Tue - NSE Expiry Shifts to Mon 2026-10-19)
    "2026-11-10",  # Diwali Laxmi Pujan (Tue - NSE Expiry Shifts to Mon 2026-11-09)
    "2026-11-24",  # Guru Nanak Jayanti (Tue - NSE Expiry Shifts to Mon 2026-11-23)
    "2026-12-25",  # Christmas (Fri)
}

# 2026 SEBI Baseline Expiry Weekday Target (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri)
SEBI_BASELINE_EXPIRY = {
    "NIFTY": 1,       # Tuesday (NSE Weekly Benchmark)
    "BANKNIFTY": 1,   # Tuesday (NSE Monthly)
    "FINNIFTY": 1,    # Tuesday (NSE Monthly)
    "MIDCPNIFTY": 1,  # Tuesday (NSE Monthly)
    "SENSEX": 3,      # Thursday (BSE Weekly Benchmark)
    "BANKEX": 3,      # Thursday (BSE Monthly)
    "CRUDEOIL": 4     # Friday (MCX Monthly Commodity)
}

class ExpiryThetaDamper:
    """Dynamic bracket adjuster with sub-microsecond in-memory holiday expiry shift evaluation"""

    def __init__(self, holidays: Optional[Set[str]] = None):
        self.holidays = holidays or DEFAULT_NSE_BSE_HOLIDAYS_2026
        self._cached_shifts: Dict[str, str] = {}

    def refresh_holidays_from_firestore(self, firestore_db = None) -> None:
        """Pulls updated dynamic holiday dates from Firestore if configured"""
        if not firestore_db:
            return
        try:
            doc = firestore_db.collection("system_config").document("market_holidays_2026").get()
            if doc.exists:
                data = doc.to_dict()
                holiday_list = data.get("holidays", [])
                if holiday_list:
                    self.holidays = set(holiday_list)
                    logger.info(f"✅ ExpiryThetaDamper: Synced {len(self.holidays)} holidays from Firestore")
        except Exception as e:
            logger.warning(f"⚠️ Firestore holiday sync warning: {e}")

    def get_authentic_expiry_date(self, symbol: str, current_dt_ist: datetime) -> datetime:
        """
        Calculates the authentic expiry date for the current week.
        If the target day is a market holiday or weekend, shifts backward to the previous trading session.
        """
        sym_u = symbol.upper()
        target_weekday = SEBI_BASELINE_EXPIRY.get(sym_u, 1)

        # 1. Determine scheduled standard expiry date in this weekly cycle
        days_ahead = target_weekday - current_dt_ist.weekday()
        if days_ahead < 0:
            days_ahead += 7  # If past target day, look at next weekly cycle

        scheduled_expiry = (current_dt_ist + timedelta(days=days_ahead)).date()

        # 2. Shift backward if scheduled expiry date is in holiday list or falls on weekend
        while scheduled_expiry.strftime("%Y-%m-%d") in self.holidays or scheduled_expiry.weekday() >= 5:
            scheduled_expiry -= timedelta(days=1)

        return datetime(scheduled_expiry.year, scheduled_expiry.month, scheduled_expiry.day)

    def is_expiry_day(self, symbol: str, current_dt_ist: Optional[datetime] = None) -> bool:
        """Returns True if today (IST) is the actual authentic expiry date (accounting for holiday shifts)"""
        if current_dt_ist is None:
            now_utc = datetime.now(timezone.utc)
            current_dt_ist = now_utc + timedelta(hours=5, minutes=30)

        actual_expiry_date = self.get_authentic_expiry_date(symbol, current_dt_ist).date()
        today_date = current_dt_ist.date()

        return today_date == actual_expiry_date

    def is_afternoon_decay_window(self, current_dt_ist: Optional[datetime] = None) -> bool:
        """Returns True between 13:00 and 15:15 IST (the critical 0 DTE theta collapse zone)"""
        if current_dt_ist is None:
            now_utc = datetime.now(timezone.utc)
            current_dt_ist = now_utc + timedelta(hours=5, minutes=30)

        hour = current_dt_ist.hour
        minute = current_dt_ist.minute
        return (hour == 13) or (hour == 14) or (hour == 15 and minute <= 15)

    def get_adapted_bracket(
        self,
        symbol: str,
        entry_premium: float,
        base_target_pct: float = 0.15,
        base_stop_loss_pct: Optional[float] = None,
        current_dt_ist: Optional[datetime] = None,
        iv: float = 0.172,
        gamma: float = 0.001
    ) -> Dict[str, Any]:
        """
        Dynamically adapts target and stop-loss on authentic expiry afternoons:
          • Normal: Target +15%, Dynamic Stop Loss (derived from IV & Gamma surface)
          • Authentic 0 DTE Afternoon (post 13:00 IST): Target tightened to +10%, Stop Loss tightened to 75% of baseline
            to capture quick bursts before rapid extrinsic decay occurs.
        """
        if current_dt_ist is None:
            now_utc = datetime.now(timezone.utc)
            current_dt_ist = now_utc + timedelta(hours=5, minutes=30)

        # Dynamic baseline stop-loss from volatility surface
        if base_stop_loss_pct is None:
            base_stop_loss_pct = round(max(0.04, (iv * 0.25) + (gamma * 15.0)), 4)

        on_expiry = self.is_expiry_day(symbol, current_dt_ist)
        in_afternoon = self.is_afternoon_decay_window(current_dt_ist)
        is_damper_active = on_expiry and in_afternoon

        if is_damper_active:
            adapted_target_pct = 0.10      # Tighten to +10% target
            adapted_stop_loss_pct = round(max(0.04, base_stop_loss_pct * 0.75), 4)   # Tighten stop loss for 0DTE theta damping
            regime = "EXPIRY_AFTERNOON_THETA_DAMPER_ACTIVE"
        else:
            adapted_target_pct = base_target_pct
            adapted_stop_loss_pct = base_stop_loss_pct
            regime = "STANDARD_INSTITUTIONAL"

        target_prem = round(entry_premium * (1.0 + adapted_target_pct), 2)
        stop_loss_prem = round(entry_premium * (1.0 - adapted_stop_loss_pct), 2)

        actual_expiry_date = self.get_authentic_expiry_date(symbol, current_dt_ist).strftime("%Y-%m-%d")

        return {
            "regime": regime,
            "is_damper_active": is_damper_active,
            "symbol": symbol.upper(),
            "target_pct": adapted_target_pct,
            "target_percent_str": f"+{adapted_target_pct * 100:.1f}%",
            "stop_loss_pct": adapted_stop_loss_pct,
            "stop_loss_percent_str": f"-{adapted_stop_loss_pct * 100:.1f}%",
            "entry_premium": entry_premium,
            "target_premium": target_prem,
            "stop_loss_premium": stop_loss_prem,
            "authentic_expiry_date": actual_expiry_date,
            "is_shifted_expiry": on_expiry and (actual_expiry_date in DEFAULT_NSE_BSE_HOLIDAYS_2026 or current_dt_ist.weekday() != SEBI_BASELINE_EXPIRY.get(symbol.upper(), 1))
        }

EXPIRY_THETA_DAMPER = ExpiryThetaDamper()
