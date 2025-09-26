"""Loop that reminds moderators about long-pending review items."""

import asyncio
import time
from datetime import datetime

import discord

from app.clients.discord_bot import bot
from app.config import (
    DISCORD_CHANNEL_ID,
    NOT_MODERATED_MINUTES,
    NOT_MODERATED_REMINDER_COOLDOWN_MINUTES,
)
from app.models.state import pending_reviews


def _format_age(minutes: float) -> str:
    """Return a human friendly age string like ``2h 15m``."""

    total_minutes = max(int(minutes), 0)
    hours, mins = divmod(total_minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


async def _send_not_moderated_card(msg_id: int, entry: dict, age_minutes: float) -> None:
    """Post a reminder embed for an item that has been pending too long."""

    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("⚠️ Not moderated reminder skipped: channel unavailable")
        return

    item = entry.get("item")
    if not item:
        return

    author = str(getattr(item, "author", "[deleted]"))
    permalink = getattr(item, "permalink", "") or ""
    reddit_link = f"https://reddit.com{permalink}" if permalink else ""
    level = entry.get("level", 0)

    embed = discord.Embed(
        title="⏰ Pending item still not moderated",
        description=f"u/{author} — {'[View on Reddit](' + reddit_link + ')' if reddit_link else 'No link available'}",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow(),
    )

    if hasattr(item, "title") and getattr(item, "title"):
        embed.add_field(name="Title", value=str(item.title)[:256], inline=False)
    elif getattr(item, "body", None):
        body = str(item.body)
        embed.add_field(name="Excerpt", value=(body[:256] + ("…" if len(body) > 256 else "")), inline=False)

    embed.add_field(name="Age", value=_format_age(age_minutes), inline=True)
    embed.add_field(name="Priority", value=f"L{level}", inline=True)

    try:
        guild_id = channel.guild.id
        discord_link = f"https://discord.com/channels/{guild_id}/{channel.id}/{msg_id}"
        embed.add_field(
            name="Review Card",
            value=f"[Open in Discord]({discord_link})",
            inline=False,
        )
    except Exception:
        pass

    embed.set_footer(text="Automatic reminder for pending moderation")

    try:
        await channel.send(embed=embed)
        print(f"⏰ Posted not-moderated reminder for Discord msg {msg_id}")
    except Exception as error:
        print(f"⚠️ Failed to send not-moderated reminder: {error}")


def not_moderated_loop() -> None:
    """Continuously watch pending reviews and send reminders when stale."""

    print("⏰ Not-moderated reminder loop started…")
    while True:
        try:
            now = time.time()
            for msg_id in list(pending_reviews.keys()):
                entry = pending_reviews.get(msg_id)
                if not entry:
                    continue

                first_seen = entry.get("first_seen_ts", entry.get("created_ts", now))
                age_minutes = (now - first_seen) / 60
                if age_minutes < NOT_MODERATED_MINUTES:
                    continue

                last_reminder = entry.get("last_reminder_ts") or 0.0
                if last_reminder and (now - last_reminder) < (
                    NOT_MODERATED_REMINDER_COOLDOWN_MINUTES * 60
                ):
                    continue

                asyncio.run_coroutine_threadsafe(
                    _send_not_moderated_card(msg_id, entry, age_minutes),
                    bot.loop,
                )
                entry["last_reminder_ts"] = now

            time.sleep(60)
        except Exception as error:
            print(f"⚠️ Not moderated loop error: {error}")
            time.sleep(30)
