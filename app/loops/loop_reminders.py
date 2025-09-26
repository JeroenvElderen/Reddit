"""Loop for scheduled Discord reminders."""

import asyncio
import time
from datetime import datetime

import discord

from app.clients.discord_bot import bot
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
    except Exception as error:  # pragma: no cover - defensive logging
        print(f"⚠️ Failed to cleanup reminders: {error}")


def _retry_after_seconds(error: discord.HTTPException, fallback: float) -> float:
    """Extract a retry delay from the exception if available."""

    retry_after = getattr(error, "retry_after", None)
    if retry_after is not None:
        try:
            return float(retry_after)
        except (TypeError, ValueError):
            pass

    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if headers and isinstance(headers, dict):
        retry_after_header = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after_header:
            try:
                return float(retry_after_header)
            except (TypeError, ValueError):
                pass

    return fallback


def _post_card(series: str, content: str) -> None:
    """Send a reminder card and register it for approval."""

    channel = bot.get_channel(DISCORD_POSTING_CHANNEL_ID)
    if not channel:
        print("⚠️ Posting channel not found")
        return

    max_attempts = 3
    backoff = 10.0

    for attempt in range(1, max_attempts + 1):
        try:
            msg = asyncio.run_coroutine_threadsafe(
                channel.send(content), bot.loop
            ).result()
            asyncio.run_coroutine_threadsafe(msg.add_reaction("✅"), bot.loop)
            asyncio.run_coroutine_threadsafe(msg.add_reaction("❌"), bot.loop)
            pending_reminders[msg.id] = {
                "series": series,
                "created_ts": time.time(),
            }
            return
        except discord.HTTPException as error:
            if error.status == 429 and attempt < max_attempts:
                delay = _retry_after_seconds(error, backoff)
                print(
                    "⚠️ Rate limited sending reminder card. "
                    f"Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts})."
                )
                time.sleep(delay)
                backoff *= 2
                continue

            print(f"⚠️ Failed to send reminder card: {error}")
            return
        except Exception as error:  # pragma: no cover - defensive logging
            print(f"⚠️ Failed to send reminder card: {error}")
            return


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
        except Exception as error:  # pragma: no cover - defensive logging
            print(f"⚠️ Reminder loop error: {error}")
        time.sleep(30)
