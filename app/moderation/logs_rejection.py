"""
Rejection logging to Discord.
"""

import discord
from app.clients.discord_bot import bot
from app.persistence.users_row import about_user_block
from app.moderation.logs_auto import get_shadow_flag
from app.utils.reddit_images import image_flag_label
from app.config import DISCORD_REJECTION_LOG_CHANNEL_ID


# =========================
# Rejection logging (with reason)
# =========================
async def log_rejection(item, old_k: int, new_k: int, flair: str, reason_text: str):
    """Log full rejection info (with reason) to the rejection log channel."""
    channel = bot.get_channel(DISCORD_REJECTION_LOG_CHANNEL_ID)
    if not channel:
        return

    author = str(item.author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    embed = discord.Embed(
        title=f"❌ Rejected {item_type}",
        description=(content[:1500] + ("... (truncated)" if len(content) > 1500 else "")),
        color=discord.Color.red(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Reason", value=reason_text, inline=False)
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k} (−1)", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    await channel.send(embed=embed)
