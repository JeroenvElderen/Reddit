"""
Achievement unlock logging.
"""

import discord
from datetime import datetime, timezone
from app.clients.discord_bot import bot
from app.config import DISCORD_ACHIEVEMENTS_CHANNEL_ID


# =========================
# Achievement logging
# =========================
async def log_achievement(username: str, badge_name: str):
    """Send an achievement unlock to the Achievements Discord channel."""
    channel = bot.get_channel(DISCORD_ACHIEVEMENTS_CHANNEL_ID)
    if not channel:
        print("⚠️ Achievements channel not found")
        return

    embed = discord.Embed(
        title="🌟 New Achievement Unlocked",
        description=f"u/{username} → **{badge_name}**",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)   # aware timestamp
    )
    await channel.send(embed=embed)
