"""
Discord command for forcing a CAH round.
"""

import discord
from discord.ext import commands
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.cah.picker import cah_enabled_packs, cah_black_card_count
from app.cah.rounds_post import create_cah_round
from app.cah.logs import log_cah_event


@bot.command(name="cahnow")
async def cahnow(ctx: commands.Context):
    """Force start a CAH round immediately."""
    active = cah_enabled_packs()
    if not active:
        await ctx.send("⚠️ No enabled packs found.")
        return

    counts = [cah_black_card_count(p["key"]) for p in active]
    if not any(c > 0 for c in counts):
        await ctx.send("⚠️ No black cards available in enabled packs.")
        return

    submission, event_title, log_text = create_cah_round(manual=True)

    await log_cah_event(event_title, log_text)

    try:
        await ctx.message.delete()   # cleanup the command message
    except Exception:
        pass


@bot.command(name="cahstats")
async def cahstats(ctx: commands.Context):
    """Display wins and participation stats from Supabase."""
    try:
        rows = (
            supabase.table("cah_rounds")
            .select("winner_username, participants")
            .execute()
            .data
            or []
        )
    except Exception:
        await ctx.send("⚠️ Unable to fetch CAH stats right now.")
        return

    wins: dict[str, int] = {}
    plays: dict[str, int] = {}
    for r in rows:
        winners = [
            w.strip()
            for w in (r.get("winner_username") or "").split(",")
            if w.strip()
        ]
        participants_raw = (
            r.get("participants")
            or r.get("participant_usernames")
            or r.get("players")
            or ""
        )
        participants = [p.strip() for p in participants_raw.split(",") if p.strip()]
        if not participants:
            participants = winners
        for p in set(participants):
            plays[p] = plays.get(p, 0) + 1
        for w in winners:
            wins[w] = wins.get(w, 0) + 1

    if not plays:
        await ctx.send("⚠️ No CAH rounds found.")
        return

    ranking = sorted(
        plays.items(),
        key=lambda kv: (wins.get(kv[0], 0), kv[1]),
        reverse=True,
    )
    lines = [
        f"{i + 1}. {user} — {wins.get(user, 0)} wins / {count} rounds"
        for i, (user, count) in enumerate(ranking[:10])
    ]
    embed = discord.Embed(
        title="🎲 CAH Stats",
        description="\n".join(lines),
        color=discord.Color.blurple(),
    )
    await ctx.reply(embed=embed, mention_author=False)