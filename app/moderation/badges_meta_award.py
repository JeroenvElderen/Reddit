"""
Award meta ladder badges.
"""

import asyncio
from datetime import datetime

from app.clients.supabase import supabase
from app.clients.reddit_owner import reddit_owner
from app.clients.discord_bot import bot
from app.models.badges_meta import META_THRESHOLDS, META_TITLES
from app.moderation.logs_achievement import log_achievement
from app.moderation.badges_award import badge_level_label, _badge_exists


def check_meta_badge(username: str, total_count: int):
    """Check meta ladder, keep only highest level, log once."""
    level = sum(1 for t in META_THRESHOLDS if total_count >= t)
    if level == 0:
        return

    base_title = META_TITLES[level - 1]
    badge_name = f"{base_title} {badge_level_label(level, len(META_THRESHOLDS))}"

    if _badge_exists(username, badge_name):
        return

    try:
        for t in META_TITLES:
            supabase.table("user_badges").delete().eq("username", username).ilike("badge", f"{t} %").execute()
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": badge_name,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"👑 Meta badge updated: {badge_name} for u/{username}")

        asyncio.run_coroutine_threadsafe(log_achievement(username, badge_name), bot.loop)

        try:
            reddit_owner.redditor(username).message(
                "👑 Meta Achievement Unlocked!",
                f"Awesome work u/{username}! You just reached **{badge_name}** 🎉"
            )
        except Exception as e:
            print(f"⚠️ Could not DM meta badge to {username}: {e}")

    except Exception as e:
        print(f"⚠️ Could not save meta badge for {username}: {e}")
