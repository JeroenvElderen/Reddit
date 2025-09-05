"""
Reddit polling loop: fetch new submissions and comments,
route them to auto-approval or manual review.
"""

import os, asyncio, discord, threading, time
from datetime import datetime, timezone

import praw

from app.clients.reddit_bot import reddit
from app.clients.discord_bot import bot
from app.clients.supabase import supabase

from app.models.state import seen_ids, add_seen_id, pending_reminders
from app.moderation.approval_awards import apply_approval_awards
from app.moderation.logs_approval import log_approval
from app.moderation.logs_auto import send_discord_auto_log
from app.moderation.cards_send import send_discord_approval
from app.persistence.users_row import ensure_user_row
from app.persistence.context_warning import get_context_warning_count
from app.moderation.context_warning import issue_context_warning
from app.utils.text_lang import likely_english
from app.utils.text_misc import item_text
from app.utils.tz import current_tz
from app.utils.night_window import in_night_guard_window
from app.persistence.users_row import already_moderated
from app.config import (
    OWNER_USERNAME,
    NIGHT_GUARD_MIN_KARMA,
    SUBREDDIT_NAME,
    DISCORD_APPROVAL_LOG_CHANNEL_ID,
    DISCORD_AUTO_APPROVAL_CHANNEL_ID,
    DISCORD_POSTING_CHANNEL_ID,
    FIXED_FLAIRS,
)


# =========================
# Routing: new items
# =========================
def handle_new_item(item):
    """Only process new, not-yet-moderated items; apply guardrails and route."""
    if item.author is None or item.id in seen_ids:
        return

    author_name = str(item.author)
    text = item_text(item)
    text_lower = text.lower()
    bot_username = os.getenv("REDDIT_USERNAME", "").lower()

    # Owner posted a welcome comment
    if (
        isinstance(item, praw.models.Comment)
        and author_name.lower() == OWNER_USERNAME
        and "welcome" in text_lower
        and "community" in text_lower
    ):
        target_user = None
        try:
            parent = item.parent()
            if parent and parent.author:
                target_user = str(parent.author)
        except Exception as e:
            print(f"⚠️ Failed to fetch parent for welcome comment {item.id}: {e}")

        if target_user:
            channel = bot.get_channel(DISCORD_POSTING_CHANNEL_ID)
            if channel:
                for msg_id, data in list(pending_reminders.items()):
                    if (
                        data.get("series") == "welcome"
                        and data.get("username", "").lower() == target_user.lower()
                    ):
                        try:
                            msg = asyncio.run_coroutine_threadsafe(
                                channel.fetch_message(msg_id), bot.loop
                            ).result()
                            asyncio.run_coroutine_threadsafe(msg.delete(), bot.loop)
                        except Exception as e:
                            print(
                                f"⚠️ Failed to delete reminder msg {msg_id} for {target_user}: {e}"
                            )
                        pending_reminders.pop(msg_id, None)
                        try:
                            asyncio.run_coroutine_threadsafe(
                                channel.send(
                                    f"💌 u/{target_user} has received a welcome message"
                                ),
                                bot.loop,
                            )
                        except Exception as e:
                            print(
                                f"⚠️ Failed to send welcome confirmation for {target_user}: {e}"
                            )
                        break
        add_seen_id(item)
        return
    
    # 👇 ensure user row in Supabase
    try:
        is_new = ensure_user_row(author_name)
        if is_new:
            # Log to Discord (fixed channel)
            channel = bot.get_channel(1410002767497527316)
            if channel:
                embed = discord.Embed(
                    title="👤 New User Detected",
                    description=f"u/{author_name} just made their first contribution!",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc),
                )
                asyncio.run_coroutine_threadsafe(channel.send(embed=embed), bot.loop)
            print(f"🆕 New user logged: u/{author_name}")

            # Queue reminder to send welcome message
            try:
                channel_rem = bot.get_channel(DISCORD_POSTING_CHANNEL_ID)
                if channel_rem:
                    msg = asyncio.run_coroutine_threadsafe(
                        channel_rem.send(
                            f"👋 Reminder: send a welcome message to u/{author_name}"
                        ),
                        bot.loop,
                    ).result()
                    asyncio.run_coroutine_threadsafe(msg.add_reaction("✅"), bot.loop)
                    asyncio.run_coroutine_threadsafe(msg.add_reaction("❌"), bot.loop)
                    pending_reminders[msg.id] = {
                        "series": "welcome",
                        "username": author_name,
                        "created_ts": time.time(),
                    }
            except Exception as e:
                print(
                    f"⚠️ Failed to queue welcome reminder for {author_name}: {e}"
                )
    except Exception as e:
        print(f"⚠️ Failed to ensure user row for {author_name}: {e}")

    if author_name.lower() == bot_username:
        print(f"🤖 skipping queue for bot's own post/comment {item.id}")
        add_seen_id(item)
        return

    # Fixed flair users bypass further checks - auto approve
    if author_name.lower() in FIXED_FLAIRS:
        add_seen_id(item)
        item.mod.approve()
        old_k, new_k, flair, total_delta, extras = apply_approval_awards(
            item, is_manual=False
        )
        extras = (extras + ", Fixed flair") if extras else "Fixed flair"
        note = f"+{total_delta}" + (f" ({extras})" if extras else "")
        print(f"✅ Auto-approved u/{author_name} ({old_k}→{new_k}) {note}")

        asyncio.run_coroutine_threadsafe(
            log_approval(item, old_k, new_k, flair, note),
            bot.loop,
        )
        if DISCORD_AUTO_APPROVAL_CHANNEL_ID != DISCORD_APPROVAL_LOG_CHANNEL_ID:
            asyncio.run_coroutine_threadsafe(
                send_discord_auto_log(
                    item, old_k, new_k, flair, total_delta, extras
                ),
                bot.loop,
            )
        return

    if already_moderated(item):
        print(f"⏩ Skipping {item.id} (already moderated)")
        add_seen_id(item)
        return

    add_seen_id(item)

    res = supabase.table("user_karma").select("*").ilike("username", author_name).execute()
    karma = int(res.data[0]["karma"]) if res.data else 0

    warnings = get_context_warning_count(author_name)
    if warnings >= 3:
        print(f"🚫 Auto-removing u/{author_name} due to {warnings} context warnings")
        try:
            item.mod.remove()
        except Exception as e:
            print(f"⚠️ Failed to remove item {getattr(item, 'id', '?')}: {e}")
        issue_context_warning(item, auto_removed=True)
        return

    # Language hinting
    if not likely_english(text):
        print("🈺 Language hint → manual")
        asyncio.run_coroutine_threadsafe(
            send_discord_approval(item, lang_label="Maybe non-English", note="Language hint"),
            bot.loop,
        )
        return

    # Night Guard
    now_local = datetime.now(current_tz())
    if in_night_guard_window(now_local) and karma < NIGHT_GUARD_MIN_KARMA:
        print(f"🌙 Night Guard: u/{author_name} ({karma} < {NIGHT_GUARD_MIN_KARMA}) → manual")
        asyncio.run_coroutine_threadsafe(
            send_discord_approval(
                item,
                lang_label="English",
                note="Night Guard window",
                night_guard_ping=True,
            ),
            bot.loop,
        )
        return

    # AUTO-APPROVE path (high karma OR bot/owner)
    if karma >= 500 or author_name.lower() in (bot_username, OWNER_USERNAME):
        item.mod.approve()
        old_k, new_k, flair, total_delta, extras = apply_approval_awards(
            item, is_manual=False
        )

        # Prevent karma/flair for the bot itself
        if author_name.lower() == bot_username:
            old_k, new_k, flair, total_delta, extras = 0, 0, "—", 0, ""

        note = f"+{total_delta}" + (f" ({extras})" if extras else "")
        print(f"✅ Auto-approved u/{author_name} ({old_k}→{new_k}) {note}")

        asyncio.run_coroutine_threadsafe(
            log_approval(item, old_k, new_k, flair, note),
            bot.loop,
        )
        if DISCORD_AUTO_APPROVAL_CHANNEL_ID != DISCORD_APPROVAL_LOG_CHANNEL_ID:
            asyncio.run_coroutine_threadsafe(
                send_discord_auto_log(
                    item, old_k, new_k, flair, total_delta, extras
                ),
                bot.loop,
            )
        return

    # Otherwise: manual review
    print(f"📨 Queueing u/{author_name} ({karma} karma) → manual")
    asyncio.run_coroutine_threadsafe(
        send_discord_approval(item, lang_label="English"),
        bot.loop,
    )


# =========================
# Main polling loop
# =========================
def reddit_polling():
    """Continuously poll Reddit inbox & subreddit for new items."""
    print("📡 Reddit polling started...")
    sub = reddit.subreddit(SUBREDDIT_NAME)
    # Always fetch existing items so that submissions or comments made while the
    # bot was offline still get processed. We rely on ``seen_ids`` to ignore
    # anything we've already handled.
    skip_existing = False

    def _submission_stream():
        for item in sub.stream.submissions(skip_existing=skip_existing):
            try:
                handle_new_item(item)
            except Exception as e:
                print(
                    f"⚠️ Error handling submission {getattr(item, 'id', '?')}: {e}"
                )
    
    def _comment_stream():
        for item in sub.stream.comments(skip_existing=skip_existing):
            try:
                handle_new_item(item)
            except Exception as e:
                print(
                    f"⚠️ Error handling comment {getattr(item, 'id', '?')} {e}"
                )
    
    threads = [
        threading.Thread(target=_submission_stream, daemon=True),
        threading.Thread(target=_comment_stream, daemon=True),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()
