"""
Close or extend CAH rounds after their lock period.
"""

import asyncio
from datetime import datetime, timedelta
from app.clients.reddit_bot import reddit
from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.cah.logs import log_cah_event
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
    if datetime.utcnow() < lock_after_dt:
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
            new_lock = datetime.utcnow() + timedelta(hours=CAH_EXTENSION_H)
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
    if datetime.utcnow() < lock_after_dt:
        return

    try:
        post.comments.replace_more(limit=0)
        comments = list(post.comments)
    except Exception:
        comments = []

    _close_with_winner(r, post, comments)


def _close_with_winner(r, post, comments):
    winner = None
    top = -1
    for c in comments:
        try:
            sc = int(getattr(c, "score", 0) or 0)
        except Exception:
            sc = 0
        if sc > top:
            top = sc
            winner = (c.author.name if c.author else None, c.id, sc)

    try:
        post.mod.lock()
    except Exception:
        pass

    supabase.table("cah_rounds").update({
        "status": "closed",
        "winner_username": winner[0] if winner else None,
        "winner_comment_id": winner[1] if winner else None,
        "winner_score": winner[2] if winner else None,
    }).eq("round_id", r["round_id"]).execute()

    asyncio.run_coroutine_threadsafe(
        log_cah_event(
            "🏆 Round Closed",
            f"Winner: u/{winner[0]} (+{winner[2]})" if winner and winner[0] else "No winner"
        ),
        bot.loop
    )


def _parse_iso(latxt: str):
    try:
        return datetime.fromisoformat(latxt.replace("Z", "+00:00")) if "Z" in latxt else datetime.fromisoformat(latxt)
    except Exception:
        return datetime.utcnow()
