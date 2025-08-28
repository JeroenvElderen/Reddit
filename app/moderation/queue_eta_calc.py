"""
Queue ETA calculation helpers.
"""

import time
from app.models.state import decision_durations, mod_activity
from app.config import (
    ETA_SAMPLE_WINDOW_MIN,
    ETA_DEFAULT_DECISION_SEC,
    ETA_ACTIVE_REVIEWER_TIMEOUT_MIN,
    ETA_MIN_SEC,
    ETA_MAX_SEC,
)


def _prune_decision_samples(now_ts: float):
    cutoff = now_ts - ETA_SAMPLE_WINDOW_MIN * 60
    # keep only recent samples
    while decision_durations and decision_durations[0][0] < cutoff:
        decision_durations.pop(0)


def _avg_decision_sec(now_ts: float) -> float:
    _prune_decision_samples(now_ts)
    if not decision_durations:
        return float(ETA_DEFAULT_DECISION_SEC)
    total = sum(d for _, d in decision_durations)
    return max(1.0, total / len(decision_durations))


def _active_reviewers(now_ts: float) -> int:
    timeout = ETA_ACTIVE_REVIEWER_TIMEOUT_MIN * 60
    return sum(1 for ts in mod_activity.values() if now_ts - ts <= timeout) or 1


def _fmt_eta_band(low_sec: int, high_sec: int) -> str:
    def f(s):
        if s >= 3600:
            h = int(round(s / 3600.0))
            return f"~{h}h"
        m = max(1, int(round(s / 60.0)))
        return f"~{m}m"
    return f"{f(low_sec)}–{f(high_sec)}"


def compute_eta_text(pending_count: int) -> str:
    now_ts = time.time()
    avg = _avg_decision_sec(now_ts)
    act = _active_reviewers(now_ts)
    raw = avg * max(1, pending_count) / max(1, act)
    raw = int(min(max(raw, ETA_MIN_SEC), ETA_MAX_SEC))
    low = int(max(ETA_MIN_SEC, raw * 0.8))
    high = int(min(ETA_MAX_SEC, raw * 1.25))
    return _fmt_eta_band(low, high)
