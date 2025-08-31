"""
Discord events: startup and reaction handling.
"""

import asyncio, threading
from app.clients.discord_bot import bot
from app.clients.reddit_bot import reddit
from app.models.state import pending_reviews, pending_spots, SUBREDDIT_NAME
from app.persistence.pending_restore import restore_pending_reviews
from app.persistence.pending_delete import delete_pending_review
from app.moderation.approval_awards import apply_approval_awards
from app.moderation.karma_apply import apply_karma_and_flair
from app.moderation.logs_approval import log_approval
from app.moderation.logs_rejection import log_rejection
from app.moderation.cards_send import send_discord_approval, _lock_and_delete_message
from app.moderation.queue_eta_record import record_mod_decision
from app.persistence.users_row import already_moderated
from app.models.ruleset import REJECTION_REASONS
from app.utils.url_parts import _get_permalink_from_embed, _fetch_item_from_permalink
from app.moderation.spots import approve_spot, reject_spot
from app.moderation.context_warning import ussie_context_warning

# loops
from app.loops.poll_reddit import reddit_polling
from app.loops.poll_dm import reddit_dm_polling
from app.loops.loop_decay import decay_loop
from app.loops.loop_sla import sla_loop
from app.loops.loop_daily_prompt import daily_prompt_poster
from app.loops.loop_daily_fact import daily_fact_poster
from app.posters.post_feedback import feedback_loop
from app.posters.post_achievements_weekly import weekly_achievements_loop
from app.loops.loop_upvotes import upvote_reward_loop
from app.loops.loop_cah import cah_loop
from app.loops.loop_pack_sched import pack_schedule_loop


@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    restore_pending_reviews()

    # background threads
    threading.Thread(target=reddit_polling, daemon=True).start()
    threading.Thread(target=reddit_dm_polling, daemon=True).start()
    threading.Thread(target=decay_loop, daemon=True).start()
    threading.Thread(target=sla_loop, daemon=True).start()
    threading.Thread(target=daily_prompt_poster, daemon=True).start()
    threading.Thread(target=daily_fact_poster, daemon=True).start()
    threading.Thread(target=feedback_loop, daemon=True).start()
    threading.Thread(target=weekly_achievements_loop, daemon=True).start()
    threading.Thread(target=upvote_reward_loop, daemon=True).start()
    threading.Thread(target=cah_loop, daemon=True).start()
    threading.Thread(target=pack_schedule_loop, daemon=True).start()


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
    
    # Stale card
    if msg_id not in pending_reviews:
        print("⚠️ Reaction on stale card.")
        if str(reaction.emoji) == "🔄":
            link = _get_permalink_from_embed(reaction.message)
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
            await send_discord_approval(item, "English", note="↻ Refreshed stale card", priority_level=0)
            try:
                await reaction.message.delete()
            except Exception:
                pass
            return
        await reaction.message.channel.send("⛔ This review card is no longer active. Click 🔄 to refresh it.")
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

    except Exception as e:
        print(f"🔥 Error handling reaction {reaction.emoji} for u/{author_name}: {e}")
