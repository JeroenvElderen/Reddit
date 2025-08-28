"""
Loop wrapper for posting daily body positivity prompt.
"""

import time
from datetime import datetime
from app.utils.tz import current_tz
from app.posters.post_prompt import post_daily_prompt


def daily_prompt_poster():
    print("🕒 Daily prompt loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            if now.hour == 12 and now.minute == 0:
                post_daily_prompt()
                time.sleep(60)  # prevent duplicate posting in the same minute
        except Exception as e:
            print(f"⚠️ Daily prompt loop error: {e}")
        time.sleep(30)
