def badge_level_label(level: int, max_level: int) -> str:
    """Return Lv.MAX if level is the last one, otherwise Lv.{n}"""
    return "Lv.MAX" if level == max_level else f"Lv.{level}"
