"""
Restore pending reviews on startup.
"""

import asyncio
from app.clients.supabase import supabase
from app.clients.reddit_bot import reddit
from app.clients.discord_bot import bot
from app.moderation.cards_send import send_discord_approval
from app.persistence.pending_delete import delete_pending_review
from app.persistence.users_row import already_moderated


# =========================
# Restore pending reviews on startup
# =========================
def restore_pending_reviews():
    rows = supabase.table("pending_reviews").select("*").execute().data or []
    for row in rows:
        try:
            # Load the original item
            if row["is_submission"]:
                item = reddit.submission(id=row["item_id"])
            else:
                item = reddit.comment(id=row["item_id"])

            # ✅ Skip if already approved/removed/banned
            if already_moderated(item):
                print(f"⏩ Skipping restore for {row['item_id']} (already moderated)")
                delete_pending_review(row["msg_id"])
                continue

            # Delete the old msg_id record (since Discord card is gone)
            delete_pending_review(row["msg_id"])

            # Re-post with RESTORED marker
            asyncio.run_coroutine_threadsafe(
                send_discord_approval(
                    item,
                    lang_label="English",
                    note="🔴 Restored after bot restart",
                    priority_level=row.get("level", 0)
                ),
                bot.loop
            )

            print(f"🔴 Restored card sent to Discord for u/{item.author} (level={row.get('level',0)})")

        except Exception as e:
            print(f"⚠️ Could not restore review {row.get('msg_id')}: {e}")
