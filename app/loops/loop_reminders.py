"""
Loop for scheduled Discord reminders.
"""

import time
import asyncio
from datetime import datetime

from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.config import DISCORD_POSTING_CHANNEL_ID
from app.models.state import pending_reminders
from app.utils.tz import current_tz


async def cleanup_old_reminders():
    """Delete previous reminder cards from the posting channel."""
    channel = bot.get_channel(DISCORD_POSTING_CHANNEL_ID)
    if not channel:
        return
    try:
        await channel.purge(limit=100, check=lambda m: m.author == bot.user)
        print("🧹 Cleaned old reminder cards")
    except Exception as e:
        print(f"⚠️ Failed to cleanup reminders: {e}")


def _post_card(series: str, content: str) -> None:
    """Send a reminder card and register it for approval."""
    channel = bot.get_channel(DISCORD_POSTING_CHANNEL_ID)
    if not channel:
        print("⚠️ Posting channel not found")
        return
    try:
        msg = asyncio.run_coroutine_threadsafe(channel.send(content), bot.loop).result()
        asyncio.run_coroutine_threadsafe(msg.add_reaction("✅"), bot.loop)
        asyncio.run_coroutine_threadsafe(msg.add_reaction("❌"), bot.loop)
        pending_reminders[msg.id] = {"series": series, "created_ts": time.time()}
    except Exception as e:
        print(f"⚠️ Failed to send reminder card: {e}")


def reminder_loop():
    """Main loop that posts scheduled reminders."""
    print("🕒 Reminder loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            if now.hour == 10 and now.minute == 0:
                _post_card("morning", "🌍 Reminder: post about country")
                time.sleep(60)
            elif now.hour == 12 and now.minute == 0:
                _post_card("lunch", "📘 Reminder: guide on nudism/naturism")
                time.sleep(60)
            elif now.hour == 14 and now.minute == 0:
                _post_card("afternoon", "✍️ Reminder: own post")
                time.sleep(60)
        except Exception as e:
            print(f"⚠️ Reminder loop error: {e}")
        time.sleep(30)