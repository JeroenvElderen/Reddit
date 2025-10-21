"""Loop for scheduled Discord reminders."""

import time

from app.clients.discord_bot import bot
from app.config import DISCORD_POSTING_CHANNEL_ID


async def cleanup_old_reminders() -> None:
    """Delete previous reminder cards from the posting channel."""
    channel = bot.get_channel(DISCORD_POSTING_CHANNEL_ID)
    if not channel:
        return
    try:
        await channel.purge(limit=100, check=lambda m: m.author == bot.user)
        print("🧹 Cleaned old reminder cards")
    except Exception as e:  # pragma: no cover - logging only
        print(f"⚠️ Failed to cleanup reminders: {e}")


def reminder_loop() -> None:
    """No-op loop placeholder for legacy scheduled reminders."""
    print("🕒 Reminder loop disabled; no scheduled posting reminders will be sent.")
    # Sleep briefly so the background thread has time to start before exiting.
    time.sleep(1)
