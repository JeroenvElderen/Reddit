def calc_quality_bonus_for_post(submission) -> int:
    if not QV_ENABLED or not hasattr(submission, "title"):
        return 0
    try:
        score = int(getattr(submission, "score", 0) or 0)
    except Exception:
        score = 0
    steps = score // max(1, QV_STEP_SCORE)
    bonus = min(QV_MAX_BONUS, steps * QV_BONUS_PER_STEP)
    return max(0, bonus)
