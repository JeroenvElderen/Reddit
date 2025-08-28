"""
Upvote reward loop (runs every 2 minutes).
"""

import time
from app.posters.post_upvotes import process_upvote_rewards


def upvote_reward_loop():
    print("🕒 Upvote reward loop started...")
    while True:
        try:
            process_upvote_rewards()
        except Exception as e:
            print(f"⚠️ Upvote reward loop error: {e}")

        time.sleep(120)
