import math, datetime, pytz
from typing import Tuple

def in_session(now_utc: datetime.datetime, open_str: str, close_str: str, tz: str) -> bool:
    tzobj = pytz.timezone(tz)
    now_local = now_utc.astimezone(tzobj)
    o = datetime.datetime.strptime(open_str, "%H:%M").time()
    c = datetime.datetime.strptime(close_str, "%H:%M").time()
    return o <= now_local.time() <= c

def compute_risk_return(curr_price: float, pred_price: float, atr: float | None, stop_mult: float = 1.5, rr_target: float = 1.8) -> Tuple[float, float, float]:
    if atr and atr > 0:
        stop = curr_price - stop_mult * atr if pred_price > curr_price else curr_price + stop_mult * atr
        target = curr_price + rr_target * (curr_price - stop) if pred_price > curr_price else curr_price - rr_target * (stop - curr_price)
    else:
        delta = 0.02 * curr_price
        stop = curr_price - delta if pred_price > curr_price else curr_price + delta
        target = curr_price + 0.036 * curr_price if pred_price > curr_price else curr_price - 0.036 * curr_price
    exp_ret = (target - curr_price) / curr_price if pred_price > curr_price else (curr_price - target) / curr_price
    return round(stop, 2), round(target, 2), float(exp_ret)
