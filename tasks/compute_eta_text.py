def compute_eta_text(pending_count: int) -> str:
    now_ts = time.time()
    avg = _avg_decision_sec(now_ts)
    act = _active_reviewers(now_ts)
    raw = avg * max(1, pending_count) / max(1, act)
    raw = int(min(max(raw, ETA_MIN_SEC), ETA_MAX_SEC))
    low = int(max(ETA_MIN_SEC, raw * 0.8))
    high = int(min(ETA_MAX_SEC, raw * 1.25))
    return _fmt_eta_band(low, high)
