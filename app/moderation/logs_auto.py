"""
Auto moderation logs + shadow flag helpers.
"""

import time, discord
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.utils.reddit_images import image_flag_label
from app.persistence.users_row import about_user_block
from app.config import DISCORD_AUTO_APPROVAL_CHANNEL_ID
from app.models.state import auto_approved


def get_shadow_flag(username: str) -> str | None:
    """Return the shadow flag note for a user, or None if not flagged."""
    try:
        res = (
            supabase.table("shadow_flags")
            .select("note")
            .ilike("username", username)
            .execute()
        )
        if res.data:
            note = (res.data[0].get("note") or "").strip()
            return note or None
    except Exception:
        pass
    return None


async def send_discord_auto_log(item, old_k, new_k, flair, awarded_points, extras_note: str = ""):
    """Send an embed to Discord logging an auto-approved post/comment."""
    channel = bot.get_channel(DISCORD_AUTO_APPROVAL_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_AUTO_APPROVAL_CHANNEL_ID)
        except Exception:
            return

    author = str(item.author)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (getattr(item, "selftext", None) if hasattr(item, "selftext") else getattr(item, "body", "")) or ""
    img_label = image_flag_label(item)

    embed = discord.Embed(
        title=f"✅ Auto-approved {item_type}",
        description=(content[:1000] + ("... (truncated)" if len(content) > 1000 else "")),
        color=discord.Color.green(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k}  (+{awarded_points})", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    if extras_note:
        embed.add_field(name="Notes", value=extras_note, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("⚠️")
    await msg.add_reaction("❌")
    await msg.add_reaction("⛔")
    auto_approved[msg.id] = {"item": item, "created_ts": time.time()}
