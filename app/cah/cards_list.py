"""
List CAH black cards with paging.
"""

import discord
from discord.ext import commands

from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.config import DISCORD_CAH_CHANNEL_ID


async def _cah_fetch_page(pack_key: str, page: int):
    try:
        res = supabase.table("cah_black_cards").select("*", count="exact") \
            .eq("pack_key", pack_key).range((page-1)*10, page*10 - 1).execute()
        rows = res.data or []
        total = res.count or 0
        total_pages = (total + 9) // 10
        return rows, total, total_pages
    except Exception as e:
        print(f"⚠️ _cah_fetch_page failed: {e}")
        return [], 0, 0


def _cah_pack_exists(pack_key: str) -> bool:
    try:
        res = supabase.table("cah_packs").select("key").eq("key", pack_key).execute()
        return bool(res.data)
    except Exception:
        return False


async def _cah_render_page_embed(ctx, pack_key: str, page: int):
    rows, total, total_pages = await _cah_fetch_page(pack_key, page)
    if total == 0:
        return await ctx.send(f"ℹ️ No cards found for pack `{pack_key}`.")

    lines = []
    for r in rows:
        t = (r['text'] or '').replace("\n", " ")
        if len(t) > 120:
            t = t[:117] + "..."
        lines.append(f"`{r['id']}` — {t}")

    embed = discord.Embed(
        title=f"🗂️ Cards in `{pack_key}` — page {page}/{total_pages}",
        description="\n".join(lines) or "—",
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"{total} total cards • use !listcards {pack_key} <page> • remove with !removecard {pack_key} <id>")
    await ctx.send(embed=embed)


# =========================
# List CAH Black Cards - Discord Bot Command
# =========================
@bot.command(name="listcards")
async def listcards(ctx, pack_key: str = None, page: str = "1"):
    """Browse all cards in a pack with paging: !listcards <pack_key> [page]"""
    try:
        if DISCORD_CAH_CHANNEL_ID and ctx.channel.id != DISCORD_CAH_CHANNEL_ID:
            return await ctx.send(f"⚠️ Please use this in <#{DISCORD_CAH_CHANNEL_ID}>.")

        if not pack_key:
            return await ctx.send("Usage: `!listcards <pack_key> [page]`")

        if not _cah_pack_exists(pack_key):
            return await ctx.send(f"❌ Unknown pack `{pack_key}`.")

        try:
            p = int(page)
        except ValueError:
            return await ctx.send("⚠️ Page must be a number.")

        await _cah_render_page_embed(ctx, pack_key, p)
    except Exception as e:
        print(f"⚠️ listcards error: {e}")
        await ctx.send("⚠️ Couldn’t list cards right now.")
