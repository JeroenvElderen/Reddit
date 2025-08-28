"""
Reddit polling loop: fetch new submissions and comments,
route them to auto-approval or manual review.
"""

import os, asyncio, discord
from datetime import datetime, timezone

from app.clients.reddit_bot import reddit
from app.clients.discord_bot import bot
from app.clients.supabase import supabase

from app.models.state import seen_ids
from app.moderation.approval_awards import apply_approval_awards
from app.moderation.logs_approval import log_approval
from app.moderation.cards_send import send_discord_approval
from app.persistence.users_row import ensure_user_row
from app.utils.text_lang import likely_english
from app.utils.text_misc import item_text
from app.utils.tz import current_tz
from app.utils.night_window import in_night_guard_window
from app.moderation.approval_base import already_moderated
from app.config import OWNER_USERNAME, NIGHT_GUARD_MIN_KARMA, SUBREDDIT_NAME


# =========================
# Routing: new items
# =========================
def handle_new_item(item):
    """Only process new, not-yet-moderated items; apply guardrails and route."""
    if item.author is None or item.id in seen_ids:
        return
    if already_moderated(item):
        print(f"⏩ Skipping {item.id} (already moderated)")
        seen_ids.add(item.id)
        return
    seen_ids.add(item.id)

    author_name = str(item.author)
    bot_username = os.getenv("REDDIT_USERNAME", "").lower()

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
    except Exception as e:
        print(f"⚠️ Failed to ensure user row for {author_name}: {e}")

    if author_name.lower() == bot_username:
        print(f"🤖 skipping queue for bot's own post/comment {item.id}")
        return

    res = supabase.table("user_karma").select("*").ilike("username", author_name).execute()
    karma = int(res.data[0]["karma"]) if res.data else 0

    # Language hinting
    text = item_text(item)
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
    for item in sub.stream.submissions(skip_existing=True):
        try:
            handle_new_item(item)
        except Exception as e:
            print(f"⚠️ Error handling submission {getattr(item, 'id', '?')}: {e}")
    for item in sub.stream.comments(skip_existing=True):
        try:
            handle_new_item(item)
        except Exception as e:
            print(f"⚠️ Error handling comment {getattr(item, 'id', '?')}: {e}")
