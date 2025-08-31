"""
Logging utilities for Cards Against Humanity events.
"""

import asyncio
import discord
from datetime import datetime, timezone
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.config import DISCORD_CAH_CHANNEL_ID


# =========================
# General CAH event logging
# =========================
async def log_cah_event(title: str, desc: str, color=discord.Color.blurple()):
    if not DISCORD_CAH_CHANNEL_ID:
        return
    channel = bot.get_channel(DISCORD_CAH_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_CAH_CHANNEL_ID)
        except Exception:
            return
    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    await channel.send(embed=embed)


# =========================
# CAH pack enable/disable prompt
# =========================
async def prompt_pack_toggle(pack_key: str, action: str, when: str, color=discord.Color.gold()):
    """
    Prompt in Discord CAH channel to enable/disable a pack.
    action = 'enable' or 'disable'
    when = human-readable date (e.g. 'Dec 1')
    """
    if not DISCORD_CAH_CHANNEL_ID:
        return None
    channel = bot.get_channel(DISCORD_CAH_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_CAH_CHANNEL_ID)
        except Exception:
            return None

    embed = discord.Embed(
        title=f"📦 {pack_key.title()} Pack {action.capitalize()}?",
        description=f"The **{pack_key.title()}** pack is scheduled to {action} on **{when}**.\n\n"
                    f"React ✅ to {action}, ❌ to skip.",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)
    )
    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            reaction.message.id == msg.id
            and not user.bot
            and str(reaction.emoji) in ["✅", "❌"]
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=86400.0, check=check)
        if str(reaction.emoji) == "✅":
            if action == "enable":
                supabase.table("cah_packs").update({"enabled": True}).eq("key", pack_key).execute()
                await log_cah_event("📦 Pack Enabled", f"Pack: **{pack_key}**")
            else:
                supabase.table("cah_packs").update({"enabled": False}).eq("key", pack_key).execute()
                await log_cah_event("📦 Pack Disabled", f"Pack: **{pack_key}**")
        else:
            await log_cah_event("⏳ Pack Change Skipped", f"Pack: **{pack_key}** left unchanged.")

        # ✅ Clean up the original prompt
        try:
            await msg.delete()
        except Exception:
            pass

    except asyncio.TimeoutError:
        await log_cah_event("⌛ No Response", f"Pack: **{pack_key}** unchanged.")
        try:
            await msg.delete()
        except Exception:
            pass


# =========================
# CAH round start prompt
# =========================
async def prompt_round_start(round_number: int, black_text: str, timeout: float = 3600.0) -> bool:
    """Prompt moderators to start a new CAH round.

    Returns True if approved, False otherwise.
    """
    channel = bot.get_channel(DISCORD_CAH_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_CAH_CHANNEL_ID)
        except Exception:
            return False

    embed = discord.Embed(
        title=f"🃏 Start CAH Round {round_number}?",
        description=f"**Black card:** {black_text}\n\nReact ✅ to approve, ❌ to skip.",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc),
    )
    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            reaction.message.id == msg.id
            and not user.bot
            and str(reaction.emoji) in ["✅", "❌"]
        )

    approved = False
    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=timeout, check=check
        )
        approved = str(reaction.emoji) == "✅"
    except asyncio.TimeoutError:
        approved = False

    if approved:
        await log_cah_event("🆕 Round Start Approved", "Moderators approved starting a new round.")
    else:
        await log_cah_event(
            "🚫 Round Start Denied", "Start of new CAH round was denied or timed out."
        )

    try:
        await msg.delete()
    except Exception:
        pass

    return approved