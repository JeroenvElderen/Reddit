def _prune_decision_samples(now_ts: float):
    cutoff = now_ts - ETA_SAMPLE_WINDOW_MIN * 60
    # keep only recent samples
    while decision_durations and decision_durations[0][0] < cutoff:
        decision_durations.pop(0)
