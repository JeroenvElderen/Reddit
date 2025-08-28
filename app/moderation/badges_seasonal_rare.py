"""
Award seasonal and rare badges.
"""

import asyncio
from datetime import datetime

from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.moderation.logs_achievement import log_achievement
from app.moderation.badges_award import _badge_exists


def check_seasonal_and_rare(username: str, row: dict):
    """Check seasonal & rare single-unlock badges (with duplicate guard + logging)."""

    # Seasonal
    seasonal_badge = "Seasonal Naturist 🍂❄️🌸☀️"
    if all([row.get("posted_in_spring"), row.get("posted_in_summer"),
            row.get("posted_in_autumn"), row.get("posted_in_winter")]) \
            and not _badge_exists(username, seasonal_badge):
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": seasonal_badge,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌟 Seasonal badge unlocked for u/{username}")
        asyncio.run_coroutine_threadsafe(log_achievement(username, seasonal_badge), bot.loop)

    # Rare: Festival
    fest_badge = "Festival Free Spirit 🎶"
    if row.get("festivals_attended", 0) >= 1 and not _badge_exists(username, fest_badge):
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": fest_badge,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🎶 Festival badge unlocked for u/{username}")
        asyncio.run_coroutine_threadsafe(log_achievement(username, fest_badge), bot.loop)

    # Rare: Traveler
    travel_badge = "Naturist Traveler 🌍"
    if row.get("countries_posted", 0) >= 5 and not _badge_exists(username, travel_badge):
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": travel_badge,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌍 Traveler badge unlocked for u/{username}")
        asyncio.run_coroutine_threadsafe(log_achievement(username, travel_badge), bot.loop)
