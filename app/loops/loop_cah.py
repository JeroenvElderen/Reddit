"""
Cards Against Humanity loop: schedule new rounds and close/extend existing ones.
"""

import time
from datetime import datetime
import os

import praw 

from app.utils.tz import current_tz
from app.cah.rounds_post import maybe_post_new_round
from app.cah.rounds_close import close_or_extend_rounds
from app.clients.reddit_bot import reddit as reddit_client
import app.clients.reddit_bot as reddit_client_module
from app.config import CAH_ENABLED, CAH_POST_HOUR


def cah_loop():
    print("🕒 CAH loop started...")
    last_post_date = None
    while True:
        try:
            if not CAH_ENABLED:
                time.sleep(60)
                continue

            now = datetime.now(current_tz())

            # Step 1: maybe post a new round
                        # Step 1: post a new round at the scheduled hour
            if now.hour >= CAH_POST_HOUR and now.date() != last_post_date:
                posted = maybe_post_new_round(now)
                if posted:
                    last_post_date = now.date()

            # Step 2: close or extend existing rounds
            close_or_extend_rounds(now)

            time.sleep(30)
        except Exception as e:
            if e.__class__.__name__ == "OAuthException":
                print("🔑 Invalid OAuth token for Reddit owner; refreshing")
                reddit_client_module.reddit = praw.Reddit(
                    client_id=os.getenv("REDDIT_CLIENT_ID"),
                    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                    username=os.getenv("REDDIT_USERNAME"),
                    password=os.getenv("REDDIT_PASSWORD"),
                    user_agent=os.getenv("REDDIT_USER_AGENT"),
                )
                continue
            print(f"⚠️ CAH loop error: {e}")
            time.sleep(60)
