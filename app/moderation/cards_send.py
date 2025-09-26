"""
Discord senders for review cards (approval queue).
"""

import time, asyncio, discord
from typing import Optional
from app.clients.discord_bot import bot
from app.models.state import pending_reviews
from app.models.ruleset import REJECTION_REASONS
from app.moderation.queue_eta_calc import compute_eta_text
from app.persistence.pending_save import save_pending_review
from app.moderation.logs_auto import send_discord_auto_log
from app.persistence.users_row import about_user_block
from app.moderation.logs_auto import get_shadow_flag
from app.utils.reddit_images import image_flag_label
from app.config import (
    DISCORD_CHANNEL_ID,
    SLA_MINUTES,
    SLA_PRIORITY_PREFIX,
    MOD_PING_ROLE_ID,
    MOD_PING_COOLDOWN_SEC,
)

_last_mod_ping_ts = 0

async def _lock_and_delete_message(msg: discord.Message):
    """Decision lock: mark as LOCKED, clear reactions, then delete after short delay."""
    try:
        embed = msg.embeds[0] if msg.embeds else None
        if embed:
            if embed.title and "🔒" not in embed.title:
                embed.title = f"🔒 {embed.title} (LOCKED)"
            embed.color = discord.Color.dark_grey()
            await msg.edit(embed=embed)
        await msg.clear_reactions()
    except Exception:
        pass
    await asyncio.sleep(2)
    try:
        await msg.delete()
    except Exception:
        pass


async def send_discord_approval(
    item,
    lang_label=None,
    note=None,
    night_guard_ping=False,
    priority_level: int = 0,
    first_seen_ts: Optional[float] = None,
    last_reminder_ts: Optional[float] = None,
):
    """Send item to Discord for manual review; supports Night Guard ping + SLA priority + ETA."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_CHANNEL_ID)
        except Exception as e:
            print(f"⚠️ Discord channel fetch failed: {e}")
            return
    if not channel:
        print("⚠️ Discord channel not found")
        return

    author = str(item.author)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    if hasattr(item, "title"):
        content = f"**{item.title}**\n\n{item.selftext or ''}"
        item_type = "Post"
        img_label = image_flag_label(item)
    else:
        content = item.body or ""
        item_type = "Comment"
        img_label = "N/A"

    title_prefix = f"{SLA_PRIORITY_PREFIX} (L{priority_level}) · " if priority_level > 0 else ""
    if note and "Restored" in note:
        title_prefix = "🔴 (RESTORED) · " + title_prefix

    embed = discord.Embed(
        title=f"{title_prefix}🧾 {item_type} Pending Review",
        description=(content[:4000] + ("... (truncated)" if len(content) > 4000 else "")),
        color=discord.Color.orange() if priority_level == 0 else discord.Color.red(),
    )
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    if lang_label:
        embed.add_field(name="Language", value=lang_label, inline=True)
    if note:
        embed.add_field(name="Note", value=note, inline=False)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    rules_overview = "\n".join([f"{emoji} {text}" for emoji, text in REJECTION_REASONS.items()])
    embed.add_field(name="Rules Overview", value=rules_overview[:1024], inline=False)

    eta_text = compute_eta_text(len(pending_reviews) + 1)
    embed.set_footer(text=f"Queue ETA: {eta_text}")

    mention = ""
    global _last_mod_ping_ts
    if night_guard_ping and MOD_PING_ROLE_ID:
        now = time.time()
        if now - _last_mod_ping_ts >= MOD_PING_COOLDOWN_SEC:
            mention = f"<@&{MOD_PING_ROLE_ID}> "
            _last_mod_ping_ts = now

    msg = await channel.send(content=mention.strip() or None, embed=embed)

    now = time.time()

    created_utc = getattr(item, "created_utc", None)
    item_created_ts = created_utc if isinstance(created_utc, (int, float)) else None
    first_seen_candidates = [ts for ts in (first_seen_ts, item_created_ts, now) if ts]
    first_seen = min(first_seen_candidates) if first_seen_candidates else now

    first_seen = first_seen_ts or now

    created_ts = now if priority_level == 0 else (now - SLA_MINUTES * 60 * priority_level)

    pending_reviews[msg.id] = {
        "item": item,
        "created_ts": created_ts,
        "last_escalated_ts": now,
        "level": priority_level,
        "first_seen_ts": first_seen,
        "last_reminder_ts": last_reminder_ts or 0.0,
    }
    save_pending_review(msg.id, item, priority_level)

    await msg.add_reaction("✅")
    await msg.add_reaction("⚠️")
    await msg.add_reaction("❌")
    await msg.add_reaction("⛔")
    await msg.add_reaction("🔄")
    print(f"📨 Sent {item_type} by u/{author} to Discord (priority={priority_level}, ETA={eta_text}, night_ping={bool(mention)})")
