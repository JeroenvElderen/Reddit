"""
Loop wrapper for daily naturist fact poster.
"""

import time
from datetime import datetime
from app.utils.tz import current_tz
from app.posters.post_fact import post_daily_fact


def daily_fact_poster():
    print("🕒 Daily fact loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            if now.hour == 8 and now.minute == 0:
                post_daily_fact()
                time.sleep(60)  # prevent double-post
        except Exception as e:
            print(f"⚠️ Daily fact loop error: {e}")
        time.sleep(30)
