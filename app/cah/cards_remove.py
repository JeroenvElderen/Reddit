"""
Interactive command to remove CAH black cards.
"""

import asyncio
import discord
from discord.ext import commands
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.config import DISCORD_CAH_CHANNEL_ID
from app.cah.logs import log_cah_event
from app.cah.cards_list import _cah_pack_exists, _cah_render_page_embed, _cah_fetch_page


# =========================
# Remove CAH Black Card - Discord Bot Command
# =========================
@bot.command(name="removecard")
@commands.has_permissions(manage_guild=True)
async def removecard(ctx, pack_key: str = None, card_id: str = None):
    """
    Remove a card by ID.
    - Direct: !removecard <pack_key> <card_id>
    - Interactive: !removecard  (then follow prompts: pack -> page -> id)
    """
    try:
        if DISCORD_CAH_CHANNEL_ID and ctx.channel.id != DISCORD_CAH_CHANNEL_ID:
            return await ctx.send(f"⚠️ Please use this in <#{DISCORD_CAH_CHANNEL_ID}>.")

        # --- Direct mode ---
        if pack_key and card_id:
            if not _cah_pack_exists(pack_key):
                return await ctx.send(f"❌ Unknown pack `{pack_key}`.")
            try:
                cid = int(card_id)
            except ValueError:
                return await ctx.send("⚠️ card_id must be a number.")

            res = supabase.table("cah_black_cards").delete() \
                .eq("pack_key", pack_key).eq("id", cid).execute()
            if getattr(res, "data", None) is not None:
                await log_cah_event("🗑️ Card Removed", f"Pack: **{pack_key}**\nCard ID: {cid}")
                await ctx.send(f"✅ Deleted card `{cid}` from `{pack_key}`")
            else:
                await ctx.send(f"⚠️ Couldn’t delete card `{cid}` (not found?).")
            return

        # --- Interactive mode ---
        prompt_msg = await ctx.send("📦 Which pack do you want to browse? (type the exact `pack_key`)")

        def check_pack(m): 
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg_pack = await bot.wait_for("message", timeout=60.0, check=check_pack)
        except asyncio.TimeoutError:
            await log_cah_event("⌛ Remove Card Timeout", f"No pack reply from {ctx.author.mention}")
            try: await prompt_msg.delete()
            except: pass
            return

        pack = msg_pack.content.strip()
        if not _cah_pack_exists(pack):
            await ctx.send(f"❌ Unknown pack `{pack}`. Cancelled.")
            try:
                await prompt_msg.delete()
                await msg_pack.delete()
            except: pass
            return

        page = 1
        await _cah_render_page_embed(ctx, pack, page)
        instr_msg = await ctx.send(
            "➡️ Type one of:\n"
            "• a **card ID** to delete\n"
            "• `next` / `prev`\n"
            "• `page <n>` (e.g. `page 3`)\n"
            "• `cancel`"
        )

        while True:
            def check_nav(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                reply = await bot.wait_for("message", timeout=120.0, check=check_nav)
            except asyncio.TimeoutError:
                await log_cah_event("⌛ Remove Card Timeout", f"No reply from {ctx.author.mention}")
                try:
                    await instr_msg.delete()
                    await msg_pack.delete()
                    await prompt_msg.delete()
                except: pass
                return

            content = reply.content.strip().lower()
            if content in ("cancel", "stop", "exit"):
                await ctx.send("❎ Cancelled.")
                try:
                    await instr_msg.delete()
                    await msg_pack.delete()
                    await prompt_msg.delete()
                    await reply.delete()
                except: pass
                return

            if content in ("next", "n", ">"):
                _, total, total_pages = await _cah_fetch_page(pack, page)
                if total_pages == 0:
                    await ctx.send("ℹ️ No cards.")
                    continue
                page = min(page + 1, total_pages)
                await _cah_render_page_embed(ctx, pack, page)
                continue

            if content in ("prev", "p", "<"):
                page = max(1, page - 1)
                await _cah_render_page_embed(ctx, pack, page)
                continue

            if content.startswith("page "):
                try:
                    want = int(content.split()[1])
                except Exception:
                    await ctx.send("⚠️ Usage: `page <number>`")
                    continue
                _, total, total_pages = await _cah_fetch_page(pack, want)
                if total_pages == 0:
                    await ctx.send("ℹ️ No cards.")
                    continue
                page = max(1, min(want, total_pages))
                await _cah_render_page_embed(ctx, pack, page)
                continue

            # otherwise, try to parse as ID and delete
            try:
                cid = int(content)
            except ValueError:
                await ctx.send("⚠️ Not understood. Reply with a card ID, `next`, `prev`, `page <n>`, or `cancel`.")
                continue

            res = supabase.table("cah_black_cards").delete() \
                .eq("pack_key", pack).eq("id", cid).execute()
            if getattr(res, "data", None) is not None:
                await log_cah_event("🗑️ Card Removed", f"Pack: **{pack}**\nCard ID: {cid}")
                await ctx.send(f"✅ Deleted card `{cid}` from `{pack}`")
                # ✅ cleanup
                try:
                    await instr_msg.delete()
                    await msg_pack.delete()
                    await prompt_msg.delete()
                    await reply.delete()
                except: pass
                return
            else:
                await ctx.send(f"⚠️ Couldn’t delete card `{cid}` (not found?). Try again.")

    except commands.MissingPermissions:
        await ctx.send("🚫 You need `Manage Server` to remove cards.")
    except Exception as e:
        print(f"⚠️ removecard error: {e}")
        await ctx.send("⚠️ Couldn’t remove cards right now.")
