"""
SLA monitor: escalate review cards with priority.
"""

import time, asyncio
from app.clients.discord_bot import bot
from app.models.state import pending_reviews
from app.moderation.cards_send import send_discord_approval
from app.config import SLA_MINUTES, SLA_PRIORITY_PREFIX, DISCORD_CHANNEL_ID


async def _escalate_card(msg_id: int):
    entry = pending_reviews.get(msg_id)
    if not entry:
        return
    item = entry["item"]
    level = entry.get("level", 0) + 1

    try:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        old_msg = await channel.fetch_message(msg_id)
        await old_msg.delete()
    except Exception:
        pass

    await send_discord_approval(
        item,
        lang_label="English",
        note=f"{SLA_PRIORITY_PREFIX}: waiting > {level * SLA_MINUTES} minutes",
        priority_level=level,
    )


def sla_loop():
    print("⏱️ SLA monitor started...")
    while True:
        try:
            now = time.time()
            for msg_id in list(pending_reviews.keys()):
                entry = pending_reviews.get(msg_id)
                if not entry:
                    continue
                last = entry.get("last_escalated_ts", entry.get("created_ts", now))
                if now - last >= SLA_MINUTES * 60:
                    entry["last_escalated_ts"] = now
                    asyncio.run_coroutine_threadsafe(_escalate_card(msg_id), bot.loop)
                    pending_reviews.pop(msg_id, None)
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ SLA loop error: {e}")
            time.sleep(30)
