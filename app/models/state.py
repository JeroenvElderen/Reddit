"""
Shared in-memory state and subreddit reference.
"""

import json
from pathlib import Path
from app.clients.reddit_bot import reddit
from app.config import SUBREDDIT_NAME

subreddit = reddit.subreddit(SUBREDDIT_NAME)

# Shared in-memory state
# pending_reviews[msg_id] = {
#     "item": praw obj,
#     "created_ts": float,
#     "last_escalated_ts": float,
#     "level": int
# }
pending_reviews = {}

# pending_spots[msg_id] = {"spot": SpotSubmission, "created_ts": float}
pending_spots = {}

# auto_approved[msg_id] = {"item": praw obj, "created_ts": float}
auto_approved = {}

_SEEN_FILE = Path("seen_ids.json")


def _load_seen_ids():
    try:
        with _SEEN_FILE.open("r") as fh:
            return set(json.load(fh))
    except Exception:
        return set()


# Track seen Reddit IDs to avoid reprocessing
seen_ids = _load_seen_ids()


def add_seen_id(item_id: str) -> None:
    """Add a Reddit ID to the seen set and persist it."""
    if item_id in seen_ids:
        return
    seen_ids.add(item_id)
    try:
        with _SEEN_FILE.open("w") as fh:
            json.dump(list(seen_ids), fh)
    except Exception as e:
        print(f"⚠️ Failed to persist seen id {item_id}: {e}")
        

# Queue ETA state
decision_durations = []   # list[(ts, duration_sec)]
mod_activity = {}         # {discord_user_id: last_action_ts}
