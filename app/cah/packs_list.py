"""
List CAH packs with their enabled/disabled status.
"""

import discord
from datetime import datetime, timezone
from discord.ext import commands
from app.clients.discord_bot import bot
from app.clients.supabase import supabase


# =========================
# List CAH Packs - Discord Bot Command
# =========================
@bot.command(name="listpacks")
@commands.has_permissions(manage_guild=True)
async def listpacks(ctx):
    """List all CAH packs with their enabled/disabled status."""
    try:
        rows = supabase.table("cah_packs").select("key, name, enabled").execute().data or []
        if not rows:
            return await ctx.send("⚠️ No packs found in Supabase.")

        lines = [
            f"- **{r['key']}** ({r['name']}) → {'✅ ENABLED' if r['enabled'] else '❌ disabled'}"
            for r in rows
        ]

        embed = discord.Embed(
            title="📦 Available CAH Packs",
            description="\n".join(lines),
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

        # delete command message to keep channel clean
        try:
            await ctx.message.delete()
        except:
            pass

    except Exception as e:
        await ctx.send(f"⚠️ Error fetching packs: {e}")
