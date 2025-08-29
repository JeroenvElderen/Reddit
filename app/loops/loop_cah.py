"""
Cards Against Humanity loop: schedule new rounds and close/extend existing ones.
"""

import time
import asyncio
from datetime import datetime

from app.utils.tz import current_tz
from app.cah.rounds_post import create_cah_round
from app.cah.rounds_close import close_or_extend_rounds
from app.cah.logs import log_cah_event
from app.clients.discord_bot import bot 
from app.clients.supabase import supabase
from app.clients.reddit_owner import create_reddit_owner
import app.clients.reddit_owner as owner_client
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

                if not open_rows and not extended_rows:
                    submission, event_title, log_text = create_cah_round()
                    asyncio.run_coroutine_threadsafe(
                        log_cah_event(event_title, log_text),
                        bot.loop,
                    )
                    last_post_date = now.date()

            # Step 2: close or extend existing rounds
            close_or_extend_rounds(now)

            time.sleep(30)
        except Exception as e:
            if e.__class__.__name__ == "OAuthException":
                print("🔑 Invalid OAuth token for Reddit owner; refreshing")
                owner_client.reddit_owner = create_reddit_owner()
                continue
            print(f"⚠️ CAH loop error: {e}")
            time.sleep(60)
