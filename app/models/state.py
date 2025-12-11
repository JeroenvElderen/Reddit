"""
Shared in-memory state and subreddit reference.
"""

import json
from pathlib import Path
import praw
from app.clients.reddit_bot import reddit
from app.config import SUBREDDIT_NAME
from app.persistence.seen_ids import load_seen_ids, save_seen_id

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

# pending_marker_actions[msg_id] = row from pending_marker_actions table
pending_marker_actions = {}

_SEEN_FILE = Path("seen_ids.json")


def _load_seen_ids():
    try:
        with _SEEN_FILE.open("r") as fh:
            local = set(json.load(fh))
    except Exception:
        local = set()
    remote = load_seen_ids()
    return local.union(remote)


# Track seen Reddit IDs to avoid reprocessing
seen_ids = _load_seen_ids()


def add_seen_id(item) -> None:
    """Add a Reddit item to the seen set and persist it."""
    item_id = getattr(item, "id", None)
    if item_id is None or item_id in seen_ids:
        return
    seen_ids.add(item_id)
    try:
        with _SEEN_FILE.open("w") as fh:
            json.dump(list(seen_ids), fh)
    except Exception as e:
        print(f"⚠️ Failed to persist seen id {item_id}: {e}")

    kind = "comment" if isinstance(item, praw.models.Comment) else "post"
    try:
        save_seen_id(item_id, kind)
    except Exception as e:
        print(f"⚠️ Failed to persist seen id {item_id} to Supabase: {e}")
        

# Queue ETA state
decision_durations = []   # list[(ts, duration_sec)]
mod_activity = {}         # {discord_user_id: last_action_ts}
