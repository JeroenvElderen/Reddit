"""
Close or extend CAH rounds after their lock period.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from app.clients.reddit_bot import reddit
from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.cah.logs import log_cah_event
from app.utils.cah_highlight import update_cah_highlight
from app.config import CAH_EXTENSION_H


def close_or_extend_rounds(now):
    """Check open and extended rounds and close/extend them when due."""
    # Handle open rounds
    rows = supabase.table("cah_rounds").select("*").eq("status", "open").execute().data or []
    for r in rows:
        _maybe_close_or_extend(r)

    # Handle extended rounds
    rows_ext = supabase.table("cah_rounds").select("*").eq("status", "extended").execute().data or []
    for r in rows_ext:
        _maybe_final_close(r)


def _maybe_close_or_extend(r):
    try:
        post = reddit.submission(id=r["post_id"])
    except Exception:
        return

    lock_after_dt = _parse_iso(r.get("lock_after_ts", ""))
    if datetime.now(timezone.utc) < lock_after_dt:
        return

    try:
        post.comments.replace_more(limit=0)
        comments = list(post.comments)
    except Exception:
        comments = []

    if r.get("comments_at_24h") is None:
        if comments:
            _close_with_winner(r, post, comments)
        else:
            # Extend round
            new_lock = datetime.now(timezone.utc) + timedelta(hours=CAH_EXTENSION_H)
            supabase.table("cah_rounds").update({
                "status": "extended",
                "comments_at_24h": 0,
                "lock_after_ts": new_lock.isoformat(),
            }).eq("round_id", r["round_id"]).execute()
            asyncio.run_coroutine_threadsafe(
                log_cah_event("⏳ Round Extended", "No comments, extended for another period."),
                bot.loop
            )


def _maybe_final_close(r):
    try:
        post = reddit.submission(id=r["post_id"])
    except Exception:
        return

    lock_after_dt = _parse_iso(r.get("lock_after_ts", ""))
    if datetime.now(timezone.utc) < lock_after_dt:
        return

    try:
        post.comments.replace_more(limit=0)
        comments = list(post.comments)
    except Exception:
        comments = []

    _close_with_winner(r, post, comments)


def _close_with_winner(r, post, comments):
    winners = []
    top = float("-inf")
    for c in comments:
        try:
            sc = int(getattr(c, "score", 0) or 0)
        except Exception:
            sc = 0
        if sc > top:
            top = sc
            winners = [(c.author.name if c.author else "[deleted]", c.id, sc)]
        elif sc == top:
            winners.append((c.author.name if c.author else "[deleted]", c.id, sc))

    try:
        post.mod.lock()
    except Exception:
        pass

    names = [w[0] for w in winners]
    ids = [w[1] for w in winners]
    supabase.table("cah_rounds").update({
        "status": "closed",
        "winner_username": ",".join(names) if winners else None,
        "winner_comment_id": ",".join(ids) if winners else None,
        "winner_score": top if winners else None,
    }).eq("round_id", r["round_id"]).execute()

    if winners:
        title = "winners" if len(winners) > 1 else "Winner"
        formatted_names = ", ".join(f"u/{n}" for n in names)
        desc = f"{title}: {formatted_names} (+{top})"
    else:
        desc = "No winner"

    asyncio.run_coroutine_threadsafe(
        log_cah_event(
            "🏆 Round Closed",
            desc
        ),
        bot.loop
    )

    # clear highlight entry for the finished round
    update_cah_highlight(None)


def _parse_iso(latxt: str):
    try:
        dt = (
            datetime.fromisoformat(latxt.replace("Z", "+00:00"))
            if "Z" in latxt
            else datetime.fromisoformat(latxt)
        )
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
