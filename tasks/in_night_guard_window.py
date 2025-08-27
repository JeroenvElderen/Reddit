def in_night_guard_window(now: datetime) -> bool:
    if not NIGHT_GUARD_ENABLED:
        return False
    start_t, end_t = _parse_window(NIGHT_GUARD_WINDOW)
    local_t = now.timetz()
    return start_t <= local_t.replace(tzinfo=None) <= end_t
