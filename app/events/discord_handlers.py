"""
Discord events: startup and reaction handling.
"""

import asyncio
import re
import threading

import discord
from datetime import datetime
from app.clients.discord_bot import bot
from app.clients.reddit_bot import reddit
from app.clients.supabase import supabase
from app.models.state import pending_reviews, pending_spots, SUBREDDIT_NAME, auto_approved, pending_marker_actions, pending_reminders
from app.persistence.pending_restore import restore_pending_reviews
from app.persistence.pending_delete import delete_pending_review
from app.moderation.approval_awards import apply_approval_awards
from app.moderation.karma_apply import apply_karma_and_flair
from app.moderation.logs_approval import log_approval
from app.moderation.logs_rejection import log_rejection
from app.moderation.logs_ban import log_ban
from app.moderation.cards_send import send_discord_approval, _lock_and_delete_message
from app.moderation.queue_eta_record import record_mod_decision
from app.persistence.users_row import already_moderated
from app.models.ruleset import REJECTION_REASONS
from app.utils.url_parts import _get_permalink_from_embed, _fetch_item_from_permalink
from app.moderation.spots import approve_spot, reject_spot
from app.moderation.context_warning import issue_context_warning
from app.config import (
    DISCORD_MAP_CHANNEL_ID,
    REPORTED_TICKETS_CATEGORY_ID,
    VERIFICATION_TICKETS_CATEGORY_ID,
)

# loops
from app.loops.poll_reddit import reddit_polling
from app.loops.poll_dm import reddit_dm_polling
from app.loops.loop_decay import decay_loop
from app.loops.loop_sla import sla_loop
from app.posters.post_feedback import feedback_loop
from app.posters.post_achievements_weekly import weekly_achievements_loop
from app.loops.loop_upvotes import upvote_reward_loop
from app.loops.loop_cah import cah_loop
from app.loops.loop_pack_sched import pack_schedule_loop
from app.loops.loop_marker_actions import marker_actions_loop
from app.loops.loop_reminders import reminder_loop, cleanup_old_reminders

def _normalize_ticket_name(prefix: str, raw_name: str) -> str:
    """Return a Discord-friendly channel name with the given prefix."""

    base = raw_name or "unknown"
    slug = re.sub(r"[^a-z0-9-]", "-", base.lower())
    slug = re.sub(r"-+", "-", slug).strip("-") or "user"
    name = f"{prefix}-{slug}"
    return name[:100]


async def _rename_ticket_channel(channel: discord.TextChannel, prefix: str) -> None:
    """Rename a Ticket Tool channel once the opener can be determined."""

    await asyncio.sleep(3)
    me = getattr(channel.guild, "me", None)
    perms = channel.permissions_for(me) if me else None
    if not perms or not perms.manage_channels:
        print(
            f"⚠️ Skipping rename for channel {channel.id}: bot lacks manage_channels permission."
        )
        return

    if not perms.view_channel:
        print(
            f"⚠️ Skipping rename for channel {channel.id}: bot lacks view_channel permission."
        )
        return

    if not perms.read_message_history:
        print(
            f"⚠️ Skipping rename for channel {channel.id}: bot lacks read_message_history permission."
        )
        return

    try:
        async for message in channel.history(limit=5):
            if message.author.bot and message.mentions:
                user = message.mentions[0]
                member = channel.guild.get_member(user.id)
                display_name = getattr(member, "display_name", None) or user.display_name or user.name
                new_name = _normalize_ticket_name(prefix, display_name)
                if channel.name != new_name:
                    try:
                        await channel.edit(name=new_name)
                    except discord.Forbidden as exc:
                        print(
                            f"⚠️ Missing permission to rename ticket channel {channel.id}: {exc}"
                        )
                        return
                    except discord.HTTPException as exc:
                        print(
                            f"🔥 Discord API error renaming ticket channel {channel.id}: {exc}"
                        )
                        return
                return
        print(f"ℹ️ No ticket opener mention found in channel {channel.id}; skipping rename.")
    except discord.Forbidden as exc:
        print(f"⚠️ Missing access while reading ticket channel {channel.id}: {exc}")
    except discord.HTTPException as exc:
        print(f"🔥 Discord API error while reading ticket channel {channel.id}: {exc}")


@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel) -> None:
    if not isinstance(channel, discord.TextChannel):
        return

    category_id = channel.category_id or 0
    prefix_map = {
        VERIFICATION_TICKETS_CATEGORY_ID: "verification",
        REPORTED_TICKETS_CATEGORY_ID: "report",
    }

    prefix = prefix_map.get(category_id)
    if prefix:
        await _rename_ticket_channel(channel, prefix)



@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    restore_pending_reviews()
    await cleanup_old_reminders()

    # background threads
    threading.Thread(target=reddit_polling, daemon=True).start()
    threading.Thread(target=reddit_dm_polling, daemon=True).start()
    threading.Thread(target=decay_loop, daemon=True).start()
    threading.Thread(target=sla_loop, daemon=True).start()
    threading.Thread(target=feedback_loop, daemon=True).start()
    threading.Thread(target=weekly_achievements_loop, daemon=True).start()
    threading.Thread(target=upvote_reward_loop, daemon=True).start()
    threading.Thread(target=cah_loop, daemon=True).start()
    threading.Thread(target=pack_schedule_loop, daemon=True).start()
    threading.Thread(target=marker_actions_loop, daemon=True).start()
    threading.Thread(target=reminder_loop, daemon=True).start()


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    print(f"➡️ Reaction received: {reaction.emoji} by {user} on msg {msg_id}")

     # Spot submissions moderation
    if msg_id in pending_spots:
        entry = pending_spots.pop(msg_id)
        spot = entry["spot"]
        if str(reaction.emoji) == "✅":
            await approve_spot(reaction.message, user, spot)
        elif str(reaction.emoji) == "❌":
            await reject_spot(reaction.message, user, spot)
        return

    if msg_id in pending_marker_actions:
        row = pending_marker_actions.pop(msg_id)
        channel = bot.get_channel(DISCORD_MAP_CHANNEL_ID) or reaction.message.channel
        action = row.get("action")
        try:
            if action == "delete" and str(reaction.emoji) == "🗑️":
                supabase.table("map_markers").delete().eq("id", row.get("marker_id")).execute()
                await channel.send(
                    f"🗑️ Deleted marker {row.get('name')} (requested by u/{row.get('username')})"
                )
            elif action == "edit" and str(reaction.emoji) == "✅":
                supabase.table("map_markers").update({
                    "name": row.get("name"),
                    "country": row.get("country"),
                    "category": row.get("category"),
                    "coordinates": row.get("coordinates"),
                    "description": row.get("description"),
                }).eq("id", row.get("marker_id")).execute()
                await channel.send(
                    f"✅ Edited marker {row.get('name')} (requested by u/{row.get('username')})"
                )
            elif str(reaction.emoji) == "❌":
                await channel.send(
                    f"❌ Rejected {action} request for marker {row.get('name')} (requested by u/{row.get('username')})"
                )
            else:
                pending_marker_actions[msg_id] = row
                return
            supabase.table("pending_marker_actions").delete().eq("id", row.get("id")).execute()
            try:
                await reaction.message.delete()
            except Exception:
                pass
        except Exception as e:
            print(f"🔥 Error handling marker action reaction: {e}")
        return

    if msg_id in pending_reminders:
        entry = pending_reminders.pop(msg_id)
        series = entry.get("series")
        if str(reaction.emoji) == "✅":
            date_str = datetime.utcnow().date().isoformat()
            if series in ("morning", "lunch"):
                res = (
                    supabase.table("scheduled_posts")
                    .select("post_number")
                    .eq("series", series)
                    .order("post_number", desc=True)
                    .limit(1)
                    .execute()
                )
                next_num = res.data[0]["post_number"] + 1 if res.data else 1
                supabase.table("scheduled_posts").insert(
                    {"series": series, "post_date": date_str, "post_number": next_num}
                ).execute()
                await reaction.message.edit(
                    content=f"{reaction.message.content}\nApproved {date_str} (Post {next_num})"
                )
            else:
                supabase.table("scheduled_posts").insert(
                    {"series": series, "post_date": date_str}
                ).execute()
                await reaction.message.edit(
                    content=f"{reaction.message.content}\nApproved {date_str}"
                )
        elif str(reaction.emoji) == "❌":
            try:
                await reaction.message.delete()
            except Exception:
                pass
        return

    if msg_id in auto_approved:
        entry = auto_approved.pop(msg_id)
        item = entry["item"]
        author_name = str(item.author)
        try:
            if str(reaction.emoji) == "⚠️":
                count = issue_context_warning(item)
                await reaction.message.channel.send(
                    f"⚠️ Warning issued to u/{author_name}. Warning {count}/3."
                )
                record_mod_decision(entry.get("created_ts"), user.id)
                await _lock_and_delete_message(reaction.message)

            elif str(reaction.emoji) == "❌":
                item.mod.remove()
                old_k, new_k, flair = apply_karma_and_flair(
                    item.author, -1, allow_negative=True
                )
                await reaction.message.channel.send(
                    f"❌ Removed u/{author_name}'s item ({old_k} → {new_k}), flair: {flair}."
                )

                review_msg = reaction.message
                for emoji in REJECTION_REASONS.keys():
                    await review_msg.add_reaction(emoji)

                def check(r, u):
                    return (
                        r.message.id == review_msg.id
                        and u.id == user.id
                        and str(r.emoji) in REJECTION_REASONS
                    )

                try:
                    reason_reaction, _ = await bot.wait_for(
                        "reaction_add", timeout=60.0, check=check
                    )
                    if str(reason_reaction.emoji) == "✏️":
                        prompt_msg = await reaction.message.channel.send(
                            f"{user.mention}, type the custom rejection reason (60s timeout):"
                        )
                        msg = await bot.wait_for(
                            "message",
                            timeout=60.0,
                            check=lambda m: m.author == user and m.channel == reaction.message.channel,
                        )
                        reason_text = f"Custom: {msg.content}"
                        try:
                            await prompt_msg.delete()
                            await msg.delete()
                        except Exception:
                            pass
                    else:
                        reason_text = REJECTION_REASONS[str(reason_reaction.emoji)]

                    try:
                        reddit.redditor(author_name).message(
                            f"❌ Your post/comment was removed from r/{SUBREDDIT_NAME}",
                            f"Reason: {reason_text}\n\nPlease review the rules before posting again.",
                        )
                    except Exception:
                        pass

                    await log_rejection(item, old_k, new_k, flair, reason_text)
                except asyncio.TimeoutError:
                    await reaction.message.channel.send(
                        "⏳ No rejection reason chosen, skipping DM/log reason."
                    )
                record_mod_decision(entry.get("created_ts"), user.id)
                await _lock_and_delete_message(reaction.message)

            elif str(reaction.emoji) == "⛔":
                item.mod.remove()
                old_k, new_k, flair = apply_karma_and_flair(
                    item.author, -1, allow_negative=True
                )
                prompt_msg = await reaction.message.channel.send(
                    f"{user.mention}, type the ban reason (5m timeout):"
                )
                try:
                    msg = await bot.wait_for(
                        "message",
                        timeout=300.0,
                        check=lambda m: m.author == user and m.channel == reaction.message.channel,
                    )
                    reason_text = msg.content
                    try:
                        await prompt_msg.delete()
                        await msg.delete()
                    except Exception:
                        pass
                except asyncio.TimeoutError:
                    reason_text = "No reason provided"
                    await reaction.message.channel.send(
                        "⏳ No ban reason provided, proceeding without reason."
                    )

                try:
                    reddit.subreddit(SUBREDDIT_NAME).banned.add(
                        author_name,
                        ban_reason=reason_text[:100],
                        ban_message=f"You are banned from r/{SUBREDDIT_NAME}: {reason_text[:1000]}",
                        note=reason_text[:300],
                    )
                except Exception:
                    pass
                try:
                    reddit.redditor(author_name).message(
                        f"⛔ You are banned from r/{SUBREDDIT_NAME}",
                        f"Reason: {reason_text}",
                    )
                except Exception:
                    pass

                await reaction.message.channel.send(
                    f"⛔ Banned u/{author_name} ({old_k} → {new_k}), flair: {flair}. Reason: {reason_text}"
                )

                record_mod_decision(entry.get("created_ts"), user.id)
                await _lock_and_delete_message(reaction.message)
                await log_ban(item, old_k, new_k, flair, reason_text)

        except Exception as e:
            print(f"🔥 Error handling auto reaction {reaction.emoji} for u/{author_name}: {e}")
        return
    
    # Stale card
    if msg_id not in pending_reviews:
        print("⚠️ Reaction on stale card → auto-refresh")
        link = await _get_permalink_from_embed(reaction.message)
        if not link:
            await reaction.message.channel.send("⚠️ I can't find the original link on this card.")
            return
        item = _fetch_item_from_permalink(link)
        if not item:
            await reaction.message.channel.send("⚠️ I couldn't reconstruct the original item from the link.")
            return
        if already_moderated(item):
            await reaction.message.channel.send("ℹ️ This item is already moderated — no need to refresh.")
            return
        await send_discord_approval(item, "English", note="↻ Auto-refreshed stale card", priority_level=0)
        try:
            await reaction.message.delete()
        except Exception:
            pass
        return

    # Active card
    entry = pending_reviews.pop(msg_id, None)
    delete_pending_review(msg_id)
    if not entry:
        print("⚠️ Missing entry for msg_id.")
        return

    item = entry["item"]
    author_name = str(item.author)

    # 🔄 refresh
    if str(reaction.emoji) == "🔄":
        level = entry.get("level", 0)
        await send_discord_approval(item, "English", note="↻ Manual refresh", priority_level=level)
        await _lock_and_delete_message(reaction.message)
        print(f"🔄 Card refreshed for u/{author_name} (level={level})")
        return

    try:
        # ✅ approve
        if str(reaction.emoji) == "✅":
            item.mod.approve()
            old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=True)
            note = f"+{total_delta}" + (f" ({extras})" if extras else "")
            await reaction.message.channel.send(
                f"✅ Approved u/{author_name} ({old_k} → {new_k}) {note}, flair: {flair}"
            )
            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)
            await log_approval(item, old_k, new_k, flair, note, extras)

        # ⚠️ warn for context
        elif str(reaction.emoji) == "⚠️":
            item.mod.approve()
            count = issue_context_warning(item)
            old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=True)
            note = f"+{total_delta}" + (f" ({extras})" if extras else "")
            await reaction.message.channel.send(
                f"⚠️ Approved u/{author_name} ({old_k} → {new_k}) {note}, flair: {flair}, Warning {count}/3."
            )
            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)
            await log_approval(item, old_k, new_k, flair, note, extras)

        # ❌ reject
        elif str(reaction.emoji) == "❌":
            item.mod.remove()
            old_k, new_k, flair = apply_karma_and_flair(item.author, -1, allow_negative=True)
            await reaction.message.channel.send(
                f"❌ Removed u/{author_name}'s item ({old_k} → {new_k}), flair: {flair}."
            )

            review_msg = reaction.message
            for emoji in REJECTION_REASONS.keys():
                await review_msg.add_reaction(emoji)

            def check(r, u):
                return r.message.id == review_msg.id and u.id == user.id and str(r.emoji) in REJECTION_REASONS

            try:
                reason_reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reason_reaction.emoji) == "✏️":
                    prompt_msg = await reaction.message.channel.send(
                        f"{user.mention}, type the custom rejection reason (60s timeout):"
                    )
                    msg = await bot.wait_for(
                        "message", timeout=60.0, check=lambda m: m.author == user and m.channel == reaction.message.channel
                    )
                    reason_text = f"Custom: {msg.content}"
                    try:
                        await prompt_msg.delete()
                        await msg.delete()
                    except Exception:
                        pass
                else:
                    reason_text = REJECTION_REASONS[str(reason_reaction.emoji)]

                try:
                    reddit.redditor(author_name).message(
                        f"❌ Your post/comment was removed from r/{SUBREDDIT_NAME}",
                        f"Reason: {reason_text}\n\nPlease review the rules before posting again."
                    )
                except Exception:
                    pass

                await log_rejection(item, old_k, new_k, flair, reason_text)
            except asyncio.TimeoutError:
                await reaction.message.channel.send("⏳ No rejection reason chosen, skipping DM/log reason.")
            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)
        # ⛔ ban
        elif str(reaction.emoji) == "⛔":
            item.mod.remove()
            old_k, new_k, flair = apply_karma_and_flair(item.author, -1, allow_negative=True)

            prompt_msg = await reaction.message.channel.send(
                f"{user.mention}, type the ban reason (5m timeout):"
            )
            try:
                msg = await bot.wait_for(
                    "message",
                    timeout=300.0,
                    check=lambda m: m.author == user and m.channel == reaction.message.channel,
                )
                reason_text = msg.content
                try:
                    await prompt_msg.delete()
                    await msg.delete()
                except Exception:
                    pass
            except asyncio.TimeoutError:
                reason_text = "No reason provided"
                await reaction.message.channel.send(
                    "⏳ No ban reason provided, proceeding without reason."
                )

            try:
                reddit.subreddit(SUBREDDIT_NAME).banned.add(
                    author_name,
                    ban_reason=reason_text[:100],
                    ban_message=f"You are banned from r/{SUBREDDIT_NAME}: {reason_text[:1000]}",
                    note=reason_text[:300],
                )
            except Exception:
                pass
            try:
                reddit.redditor(author_name).message(
                    f"⛔ You are banned from r/{SUBREDDIT_NAME}",
                    f"Reason: {reason_text}",
                )
            except Exception:
                pass

            await reaction.message.channel.send(
                f"⛔ Banned u/{author_name} ({old_k} → {new_k}), flair: {flair}. Reason: {reason_text}"
            )

            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)
            await log_ban(item, old_k, new_k, flair, reason_text)

    except Exception as e:
        print(f"🔥 Error handling reaction {reaction.emoji} for u/{author_name}: {e}")
