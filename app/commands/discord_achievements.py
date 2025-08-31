"""
Discord command for posting weekly achievements on demand.
"""

from discord.ext import commands
from app.clients.discord_bot import bot
from app.posters.post_achievements_weekly import post_weekly_achievements


@bot.command(name="achievementsnow")
async def achievementsnow(ctx: commands.Context):
    """Post the weekly achievements digest immediately."""
    try:
        posted = post_weekly_achievements()
    except Exception:
        await ctx.send("⚠️ Could not post weekly achievements right now.")
        return

    if posted:
        await ctx.send("✅ Weekly achievements digest posted.")
    else:
        await ctx.send("ℹ️ No new weekly achievements to post.")

    try:
        await ctx.message.delete()  # cleanup
    except Exception:
        pass