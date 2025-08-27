def _active_reviewers(now_ts: float) -> int:
    timeout = ETA_ACTIVE_REVIEWER_TIMEOUT_MIN * 60
    return sum(1 for ts in mod_activity.values() if now_ts - ts <= timeout) or 1
