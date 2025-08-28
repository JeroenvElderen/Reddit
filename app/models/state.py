"""
Shared in-memory state and subreddit reference.
"""

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

# Track seen Reddit IDs to avoid reprocessing
seen_ids = set()

# Queue ETA state
decision_durations = []   # list[(ts, duration_sec)]
mod_activity = {}         # {discord_user_id: last_action_ts}
