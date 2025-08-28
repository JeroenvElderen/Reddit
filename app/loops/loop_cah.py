"""
Cards Against Humanity loop: schedule new rounds and close/extend existing ones.
"""

import time
from datetime import datetime
from app.utils.tz import current_tz
from app.cah.rounds_post import maybe_post_new_round
from app.cah.rounds_close import close_or_extend_rounds
from app.config import CAH_ENABLED


def cah_loop():
    print("🕒 CAH loop started...")
    while True:
        try:
            if not CAH_ENABLED:
                time.sleep(60)
                continue

            now = datetime.now(current_tz())

            # Step 1: maybe post a new round
            maybe_post_new_round(now)

            # Step 2: close or extend existing rounds
            close_or_extend_rounds(now)

            time.sleep(30)
        except Exception as e:
            print(f"⚠️ CAH loop error: {e}")
            time.sleep(60)
