"""
Karma stats helpers.
"""
from collections import defaultdict 
import asyncio

from app.clients.supabase import supabase
from app.clients.reddit_bot import reddit


# =========================
# User stats fetcher
# =========================
def get_user_stats(username: str):
    """Fetch stats for a given user from Supabase."""
    try:
        res = supabase.table("user_karma").select("*").ilike("username", username).execute()
        if not res.data:
            return None
        row = res.data[0]
        return {
            "karma": int(row.get("karma", 0)),
            "flair": row.get("last_flair", "Needs Growth"),
            "streak": int(row.get("streak_days", 0)),
            "last_post": row.get("last_approved_date"),
        }
    except Exception as e:
        print(f"⚠️ Stats lookup failed for {username}: {e}")
        return None


# =========================
# get last approved item
# =========================
def get_last_approved_item(username: str):
    """Return (text, is_post) of the last approved post/comment, or (None, None)."""
    try:
        redditor = reddit.redditor(username)  # use bot session to check history

        # Check posts first
        for sub in redditor.submissions.new(limit=20):
            if getattr(sub, "approved", False):
                return sub.title, True

        # If no approved posts, check comments
        for com in redditor.comments.new(limit=20):
            if getattr(com, "approved", False):
                snippet = com.body.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                return snippet, False
    except Exception as e:
        print(f"⚠️ Could not fetch last approved item for {username}: {e}")

    return None, None
