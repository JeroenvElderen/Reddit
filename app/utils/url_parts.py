"""
Permalink + URL parsing helpers.
"""

from urllib.parse import urlparse
import discord
from app.clients.reddit_bot import reddit

def _get_permalink_from_embed(msg: discord.Message) -> str | None:
    try:
        emb = msg.embeds[0] if msg.embeds else None
        if not emb or not emb.fields:
            return None
        for f in emb.fields:
            if f.name.lower() == "link":
                return (f.value or "").strip()
    except Exception:
        pass
    return None

def _fetch_item_from_permalink(url: str):
    """
    Given a permalink like https://reddit.com/r/sub/comments/POSTID/title/COMMENTID/
    return the PRAW object (submission or comment).
    """
    try:
        p = urlparse(url)
        parts = [x for x in p.path.split("/") if x]
        if "comments" in parts:
            i = parts.index("comments")
            post_id = parts[i + 1]
            comment_id = parts[-1] if len(parts) > i + 3 else None
            if comment_id and comment_id != post_id and len(comment_id) in (7, 8):
                return reddit.comment(id=comment_id)
            return reddit.submission(id=post_id)
    except Exception:
        pass
    return None
