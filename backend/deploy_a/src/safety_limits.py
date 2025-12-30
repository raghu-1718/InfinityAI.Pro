# backend/engine-a/src/safety_limits.py

# Currency: INR

MAX_TRADE_CAPITAL = 500_000        # ₹5,00,000 per trade
MAX_SESSION_CAPITAL = 2_000_000    # ₹20,00,000 per session

MAX_DAILY_LOSS = -100_000          # Example daily loss cap
MAX_CONSECUTIVE_LOSSES = 3

KILL_SWITCH_REASONS = {
    "MAX_TRADE_LIMIT",
    "MAX_SESSION_LIMIT",
    "MAX_DRAWDOWN",
    "CONSECUTIVE_LOSSES",
    "MANUAL_HALT",
    "ANOMALY_DETECTED"
}
