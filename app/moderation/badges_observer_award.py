"""
Award Quiet Observer ladder badges.
"""

import asyncio
from datetime import datetime

from app.clients.supabase import supabase
from app.clients.reddit_owner import reddit_owner
from app.clients.discord_bot import bot
from app.moderation.logs_achievement import log_achievement
from app.moderation.badges_award import _badge_exists


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


def award_badge(username: str, badge_name: str):
    """Generic badge award helper (Observer ladder), with duplicate guard + logging."""
    if _badge_exists(username, badge_name):
        return

    try:
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": badge_name,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌙 Observer badge unlocked: {badge_name} for u/{username}")

        # ✅ Log to Discord
        asyncio.run_coroutine_threadsafe(log_achievement(username, badge_name), bot.loop)

        # Optional: DM user from owner account
        try:
            reddit_owner.redditor(username).message(
                "🌙 New Observer Achievement!",
                f"Congrats u/{username}! You just earned **{badge_name}** 🏆\n\n"
                f"Your time as an Observer is part of your naturist journey 🌿"
            )
        except Exception as e:
            print(f"⚠️ Could not DM Observer badge to {username}: {e}")

    except Exception as e:
        print(f"⚠️ Could not save Observer badge for {username}: {e}")
