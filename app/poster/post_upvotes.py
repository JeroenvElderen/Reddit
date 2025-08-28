"""
Upvote reward processor: credit OPs for upvotes.
"""

from app.models.state import subreddit
from app.features.upvote_credit import credit_upvotes_for_submission


def process_upvote_rewards(limit: int = 100):
    """Scan fresh posts and credit upvotes to OPs."""
    for sub in subreddit.new(limit=limit):
        try:
            # only process approved posts
            if not getattr(sub, "approved", False):
                continue
            credit_upvotes_for_submission(sub)
        except Exception as e:
            print(f"⚠️ Upvote credit per-post error: {e}")
