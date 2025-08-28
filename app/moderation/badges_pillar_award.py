"""
Award badges for pillar ladders (body, travel, mind, advocacy).
"""

import asyncio
from datetime import datetime

from app.clients.supabase import supabase
from app.clients.reddit_owner import reddit_owner
from app.clients.discord_bot import bot
from app.models.badges_pillars import PILLAR_THRESHOLDS
from app.moderation.logs_achievement import log_achievement
from app.moderation.badges_award import badge_level_label, _badge_exists


def check_pillar_badge(username: str, field: str, count: int):
    """Check pillar ladders, keep only highest level, log once."""
    level = sum(1 for t in PILLAR_THRESHOLDS if count >= t)
    if level == 0:
        return

    base = field.replace("_posts_count", "").replace("_", " ").title()
    badge_name = f"{base} {badge_level_label(level, len(PILLAR_THRESHOLDS))}"

    if _badge_exists(username, badge_name):
        return

    try:
        supabase.table("user_badges").delete().eq("username", username).ilike("badge", f"{base} %").execute()
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": badge_name,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌟 Pillar badge updated: {badge_name} for u/{username}")

        # log to Discord
        asyncio.run_coroutine_threadsafe(log_achievement(username, badge_name), bot.loop)

        # optional DM to user
        try:
            reddit_owner.redditor(username).message(
                "🌟 New Naturist Achievement!",
                f"Congrats u/{username}! You just reached **{badge_name}** 🏆\n\n"
                f"Keep growing your naturist journey 🌿"
            )
        except Exception as e:
            print(f"⚠️ Could not DM pillar badge to {username}: {e}")

    except Exception as e:
        print(f"⚠️ Could not save pillar badge for {username}: {e}")
