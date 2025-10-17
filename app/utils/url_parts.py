"""
Permalink + URL parsing helpers.
"""

import re
from urllib.parse import urlparse
import discord
from app.clients.reddit_bot import reddit

_REDDIT_URL_RE = re.compile(r"https?://(?:www\.)?(?:reddit\.com|redd\.it)[^\s<>]*", re.IGNORECASE)


async def _get_permalink_from_embed(msg: discord.Message) -> str | None:
    try:
        message = msg
        embeds = getattr(message, "embeds", None) or []
        if not embeds and getattr(message, "channel", None):
            try:
                fetched = await message.channel.fetch_message(message.id)
                if fetched:
                    message = fetched
                    embeds = getattr(message, "embeds", None) or []
            except Exception:
                embeds = []

        for emb in embeds:
            fields = getattr(emb, "fields", None)
            if fields:
                for f in fields:
                    if getattr(f, "name", "").lower() == "link":
                        value = (getattr(f, "value", "") or "").strip().strip("<>")
                        if value:
                            return value
            url = getattr(emb, "url", None)
            if url:
                url = str(url).strip().strip("<>")
                if url:
                    return url

        content = getattr(message, "content", "") or ""
        if content:
            match = _REDDIT_URL_RE.search(content)
            if match:
                return match.group(0).strip("<>")
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
