"""
Queue ETA recording helpers.
"""

import time
from app.models.state import decision_durations, mod_activity


def record_mod_decision(created_ts: float, discord_user_id: int):
    now_ts = time.time()
    duration = max(1.0, now_ts - float(created_ts or now_ts))
    decision_durations.append((now_ts, duration))
    mod_activity[discord_user_id] = now_ts
