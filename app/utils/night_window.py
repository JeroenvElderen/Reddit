"""
Night Guard window utilities.
"""

from datetime import time as dtime, datetime
from app.config import NIGHT_GUARD_ENABLED, NIGHT_GUARD_WINDOW

def _parse_window(s: str):
    a, b = s.split("-")
    h1, m1 = map(int, a.split(":"))
    h2, m2 = map(int, b.split(":"))
    return dtime(h1, m1), dtime(h2, m2)

def in_night_guard_window(now: datetime) -> bool:
    if not NIGHT_GUARD_ENABLED:
        return False
    start_t, end_t = _parse_window(NIGHT_GUARD_WINDOW)
    local_t = now.timetz()
    return start_t <= local_t.replace(tzinfo=None) <= end_t
