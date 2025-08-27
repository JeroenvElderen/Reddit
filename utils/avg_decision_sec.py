def _avg_decision_sec(now_ts: float) -> float:
    _prune_decision_samples(now_ts)
    if not decision_durations:
        return float(ETA_DEFAULT_DECISION_SEC)
    total = sum(d for _, d in decision_durations)
    return max(1.0, total / len(decision_durations))
