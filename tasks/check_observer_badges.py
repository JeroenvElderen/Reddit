def check_observer_badges(username: str, row: dict):
    """Check and award Quiet Observer achievement ladders."""
    # --- Patience ---
    patience_thresholds = [7, 30, 90]
    patience_badges = ["Still Waters 🪷", "Deep Reflection 🪷", "Silent Strength 🪷"]
    for i, t in enumerate(patience_thresholds):
        if row.get("observer_days", 0) >= t:
            award_badge(username, f"{patience_badges[i]} Lv.{i+1 if i < 2 else 'MAX'}")

    # --- Contribution ---
    contrib_thresholds = [1, 5, 20]
    contrib_badges = ["Quiet Voice 🗣️", "Gentle Helper 💚", "Guiding Light 🌟"]
    for i, t in enumerate(contrib_thresholds):
        if row.get("observer_comments_count", 0) >= t:
            award_badge(username, f"{contrib_badges[i]} Lv.{i+1 if i < 2 else 'MAX'}")

    # --- Growth ---
    growth_thresholds = [1, 3, 5]
    growth_badges = ["First Step 🌱", "Comeback Trail 👣", "Resilient Spirit ✨"]
    for i, t in enumerate(growth_thresholds):
        if row.get("observer_exits_count", 0) >= t:
            award_badge(username, f"{growth_badges[i]} Lv.{i+1 if i < 2 else 'MAX'}")

    # --- Community Support ---
    support_thresholds = [10, 50, 200]
    support_badges = ["Friendly Observer 🤝", "Encourager 🌿", "Community Whisper ✨"]
    for i, t in enumerate(support_thresholds):
        if row.get("observer_upvotes_total", 0) >= t:
            award_badge(username, f"{support_badges[i]} Lv.{i+1 if i < 2 else 'MAX'}")
