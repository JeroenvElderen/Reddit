"""
Approval logging to Discord.
"""

import discord
from app.clients.discord_bot import bot
from app.persistence.users_row import about_user_block
from app.moderation.logs_auto import get_shadow_flag
from app.utils.reddit_images import image_flag_label
from app.config import DISCORD_APPROVAL_LOG_CHANNEL_ID


# =========================
# Approval logging
# =========================
async def log_approval(item, old_k: int, new_k: int, flair: str, note: str, extras: str = ""):
    """Log full approval info to the approval log channel."""
    channel = bot.get_channel(DISCORD_APPROVAL_LOG_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_APPROVAL_LOG_CHANNEL_ID)
        except Exception as e:
            print(f"⚠️ Could not fetch approval log channel: {e}")
            return
    if not channel:
        print("⚠️ Approval log channel not found.")
        return

    author = str(item.author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    embed = discord.Embed(
        title=f"✅ Approved {item_type}",
        description=(content[:1500] + ("... (truncated)" if len(content) > 1500 else "")),
        color=discord.Color.green(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k} {note}", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    if extras:
        embed.add_field(name="Notes", value=extras, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    await channel.send(embed=embed)
