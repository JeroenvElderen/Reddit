"""
CAH round creation (scheduled/manual).
"""

import uuid
from datetime import datetime, timedelta
from app.clients.supabase import supabase
from app.clients.reddit_owner import reddit_owner
from app.models.state import SUBREDDIT_NAME
from app.config import CAH_POST_FLAIR_ID, CAH_ROUND_DURATION_H
from app.cah.picker import cah_pick_black_card
from app.cah.logs import log_cah_event


def create_cah_round(manual: bool = False):
    """Create a new CAH round and post to Reddit."""
    black = cah_pick_black_card()
    title = "🎲 CAH Round — Fill in the Blank!"
    submission = reddit_owner.subreddit(SUBREDDIT_NAME).submit(
        title, selftext=f"**Black card:** {black}"
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
    start_ts = datetime.utcnow()
    lock_after = start_ts + timedelta(hours=CAH_ROUND_DURATION_H)

    supabase.table("cah_rounds").insert({
        "round_id": round_id,
        "post_id": submission.id,
        "black_text": black,
        "start_ts": start_ts.isoformat(),
        "status": "open",
        "lock_after_ts": lock_after.isoformat(),
    }).execute()

    event_title = "🎲 New Round (manual)" if manual else "🎲 New Round Posted"
    log_text = f"Black card: **{black}**\n[Reddit link](https://reddit.com{submission.permalink})"
    return submission, event_title, log_text
