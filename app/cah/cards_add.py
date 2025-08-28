"""
Interactive command to add CAH black cards.
"""

import asyncio
import discord
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.cah.logs import log_cah_event


# =========================
# Add CAH Black Card - Discord Bot Command
# =========================
@bot.command(name="addcard")
async def addcard(ctx):
    """Interactive flow to add a CAH black card to Supabase."""
    rows = supabase.table("cah_packs").select("key, name, enabled").execute().data or []
    pack_lines = [
        f"- **{r['key']}** ({r['name']}) → {'ENABLED ✅' if r['enabled'] else 'disabled ❌'}"
        for r in rows
    ]
    embed = discord.Embed(
        title="📝 Add a new CAH Black Card",
        description=(
            "Reply in this channel with:\n\n"
            "`pack_key | card text`\n\n"
            "`You can send multiple lines to add several cards at once.\n\n"
            "**Example:**\n"
            "`summer | Nothing says naturism like ____.`\n\n"
            "⚠️ Use `____` for blanks!\n\n"
            "**Available Packs:**\n" + "\n".join(pack_lines)
        ),
        color=discord.Color.blurple()
    )
    prompt_msg = await ctx.send(embed=embed)

    def check(m):
        return m.author == ctx.author and "|" in m.content and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", timeout=120.0, check=check)
        lines = [l.strip() for l in msg.content.splitlines() if l.strip()]
        records = []
        failed = []

        for idx, line in enumerate(lines, start=1):
            if "|" not in line:
                failed.append(f"Line {idx}: Missinng '|'.")
                continue
            pack_key, card_text = [p.strip() for p in line.split("|", 1)]

            pack = (
                supabase.table("cah_packs")
                .select("*")
                .eq("key", pack_key)
                .execute()
            )
            if not pack.data:
                failed.append(f"Line {idx}: '{pack_key}' not found.")
                continue

            if "____" not in card_text:
                failed.append(
                    f"Line {idx}: Card text must contain at least one'____' blank."
                )
                continue
            records.append({"pack_key": pack_key, "text": card_text})

        res = None
        if records:
            res = supabase.table("cah_black_cards").insert(records).execute()
            for rec in records:
                await log_cah_event(
                    "🆕 Card Added", f"Pack: **{rec['pack_key']}**\nText: {rec['text']}"
                )
        
        if failed:
            for msg_text in failed:
                await log_cah_event("⚠️ Add Card Failed", msg_text)
        
        summary = []
        if records:
            summary.append(f"✅ Added {len(records)} card(s).")
        if failed:
            summary.append("⚠️ Failed lines:\n" + "\n".join(failed))
        await ctx.send("\n".join(summary) or "No valid lines provided.")

    except asyncio.TimeoutError:
        await log_cah_event("⌛ Add Card Timeout", f"No reply from {ctx.author.mention}")

    finally:
        # ✅ clean up both prompt + user reply
        try:
            await prompt_msg.delete()
        except:
            pass
        try:
            await msg.delete()
        except:
            pass
