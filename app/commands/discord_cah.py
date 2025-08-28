"""
Discord command for forcing a CAH round.
"""

from discord.ext import commands
from app.clients.discord_bot import bot
from app.cah.picker import cah_enabled_packs
from app.cah.rounds_post import create_cah_round
from app.cah.logs import log_cah_event


@bot.command(name="cahnow")
async def cahnow(ctx: commands.Context):
    """Force start a CAH round immediately."""
    active = cah_enabled_packs()
    if not active:
        await ctx.send("⚠️ No enabled packs found.")
        return

    total_cards = 0
    for p in active:
        cnt = (
            p.get("count") or 0
            or 0  # safety default
        )
        total_cards += cnt
    if total_cards <= 0:
        await ctx.send("⚠️ No black cards available in enabled packs.")
        return

    submission, event_title, log_text = create_cah_round(manual=True)

    await log_cah_event(event_title, log_text)

    try:
        await ctx.message.delete()   # cleanup the command message
    except Exception:
        pass
