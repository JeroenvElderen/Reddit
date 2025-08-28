"""
CAH round creation (scheduled/manual).
"""

import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from app.clients.supabase import supabase
from app.clients.reddit_owner import reddit_owner
from app.clients.discord_bot import bot
from app.models.state import SUBREDDIT_NAME
from app.config import CAH_POST_FLAIR_ID, CAH_ROUND_DURATION_H
from app.cah.picker import cah_pick_black_card
from app.cah.logs import log_cah_event
from app.cah.templates import format_cah_body



def create_cah_round(manual: bool = False):
    """Create a new CAH round and post to Reddit."""
    rows = supabase.table("cah_rounds").select("Round_id").execute()
    next_round = len(rows.data or []) + 1
    black = cah_pick_black_card()
    title = "🎲 CAH Round {next_round} — Fill in the Blank!"
    selftext = format_cah_body(next_round, black, CAH_ROUND_DURATION_H)

    submission = reddit_owner.subreddit(SUBREDDIT_NAME).submit(
        title, selftext=selftext
    )

    if CAH_POST_FLAIR_ID:
        try:
            submission.flair.select(CAH_POST_FLAIR_ID)
        except Exception:
            pass

    try:
        submission.mod.approve()
    except Exception:
        pass

    round_id = str(uuid.uuid4())
    start_ts = datetime.now(timezone.utc)
    lock_after = start_ts + timedelta(hours=CAH_ROUND_DURATION_H)

    supabase.table("cah_rounds").insert({
        "round_id": round_id,
        "round_number": next_round,
        "post_id": submission.id,
        "black_text": black,
        "start_ts": start_ts.isoformat(),
        "status": "open",
        "lock_after_ts": lock_after.isoformat(),
    }).execute()

    event_title = "🎲 New Round (manual)" if manual else "🎲 New Round Posted"
    log_text = f"Black card: **{black}**\n[Reddit link](https://reddit.com{submission.permalink})"
    return submission, event_title, log_text



def maybe_post_new_round(now: datetime):
    """Post a new round if none are currently active."""
    try:
        open_rows = (
            supabase.table("cah_rounds")
            .select("round_id")
            .eq("status", "open")
            .execute()
            .data
            or []
        )
    except Exception:
        open_rows = []

    if open_rows:
        return

    try:
        extended_rows = (
            supabase.table("cah_rounds")
            .select("round_id")
            .eq("status", "extended")
            .execute()
            .data
            or []
        )
    except Exception:
        extended_rows = []

    if extended_rows:
        return

    submission, event_title, log_text = create_cah_round()
    asyncio.run_coroutine_threadsafe(
        log_cah_event(event_title, log_text),
        bot.loop,
    )
