import datetime
import pytz
from typing import Tuple


def in_session(
    now_utc: datetime.datetime,
    open_str: str,
    close_str: str,
    tz: str
) -> bool:
    tzobj = pytz.timezone(tz)
    now_local = now_utc.astimezone(tzobj)

    open_t = datetime.datetime.strptime(open_str, "%H:%M").time()
    close_t = datetime.datetime.strptime(close_str, "%H:%M").time()

    return open_t <= now_local.time() <= close_t


def compute_risk_return(
    curr_price: float,
    pred_price: float,
    atr: float | None,
    stop_mult: float = 1.5,
    rr_target: float = 1.8
) -> Tuple[float, float, float]:
    """
    Compute stop-loss, target and expected return.

    Explicit, symmetric, auditable logic.
    """
    is_long = pred_price > curr_price
    direction = 1 if is_long else -1

    if atr and atr > 0:
        stop_distance = max(stop_mult * atr, 0.005 * curr_price)
    else:
        stop_distance = 0.02 * curr_price

    stop = curr_price - direction * stop_distance
    target = curr_price + direction * rr_target * stop_distance

    exp_ret = abs(target - curr_price) / curr_price

    return (
        round(stop, 2),
        round(target, 2),
        round(float(exp_ret), 6),
    )
