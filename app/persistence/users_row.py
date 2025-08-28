"""
User info helpers.
"""

from datetime import datetime, timezone
from app.clients.supabase import supabase
from app.clients.reddit_bot import reddit


# ---------- About snapshot ----------
def about_user_block(name: str):
    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
    sub_karma = int(res.data[0]["karma"]) if res.data else 0
    try:
        rd = reddit.redditor(name)
        created = getattr(rd, "created_utc", None)
        days = int((datetime.now(timezone.utc).timestamp() - created) / 86400) if created else "—"
    except Exception:
        days = "—"
    return sub_karma, days


# ---------- Moderation checks ----------
def already_moderated(item) -> bool:
    if getattr(item, "approved_by", None):
        return True
    if getattr(item, "removed_by_category", None) is not None:
        return True
    if getattr(item, "banned_by", None):
        return True
    if getattr(item, "author", None) is None:
        return True
    return False
