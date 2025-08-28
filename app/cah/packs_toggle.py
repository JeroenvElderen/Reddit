"""
Enable/disable CAH packs.
"""

from discord.ext import commands
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.cah.logs import log_cah_event


# =========================
# Enable/Disable CAH Pack - Discord Bot Command
# =========================
@bot.command(name="enablepack")
@commands.has_permissions(manage_guild=True)
async def enablepack(ctx, pack_key: str = None):
    """Enable a CAH pack (so its cards can be used)."""
    try:
        if not pack_key:
            return await ctx.send("⚠️ Usage: `!enablepack <pack_key>`")

        res = supabase.table("cah_packs").update({"enabled": True}).eq("key", pack_key).execute()
        if res.data:
            await log_cah_event("📦 Pack Enabled", f"Pack: **{pack_key}**")
        else:
            await log_cah_event("⚠️ Enable Pack Failed", f"Pack: **{pack_key}** not found.")
    finally:
        try:
            await ctx.message.delete()   # ✅ cleanup
        except:
            pass


@bot.command(name="disablepack")
@commands.has_permissions(manage_guild=True)
async def disablepack(ctx, pack_key: str = None):
    """Disable a CAH pack (its cards won’t be picked)."""
    try:
        if not pack_key:
            return await ctx.send("⚠️ Usage: `!disablepack <pack_key>`")

        res = supabase.table("cah_packs").update({"enabled": False}).eq("key", pack_key).execute()
        if res.data:
            await log_cah_event("📦 Pack Disabled", f"Pack: **{pack_key}**")
        else:
            await log_cah_event("⚠️ Disable Pack Failed", f"Pack: **{pack_key}** not found.")
    finally:
        try:
            await ctx.message.delete()   # ✅ cleanup
        except:
            pass
