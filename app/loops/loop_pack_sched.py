"""
Pack schedule loop: enable/disable packs automatically.
"""

import time, asyncio
from datetime import datetime, date
from app.clients.discord_bot import bot
from app.models.schedules import PACK_SCHEDULE
from app.cah.packs_toggle import prompt_pack_toggle
from app.utils.tz import current_tz


def pack_schedule_loop():
    print("🕒 Pack schedule loop started...")
    while True:
        try:
            today = datetime.now(current_tz()).date()
            m, d = today.month, today.day

            for pack_key, schedule in PACK_SCHEDULE.items():
                start_m, start_d = schedule["start"]
                end_m, end_d = schedule["end"]

                start = date(today.year, start_m, start_d)
                end = date(today.year, end_m, end_d)

                # Handle wrap-around (cross-year schedules, e.g., winter packs)
                if end < start:
                    if m >= start_m:  # late in year
                        end = date(today.year + 1, end_m, end_d)
                    else:
                        start = date(today.year - 1, start_m, start_d)

                # 3 days before start
                if (start - today).days == 3:
                    asyncio.run_coroutine_threadsafe(
                        prompt_pack_toggle(pack_key, "enable", start.strftime("%b %d")),
                        bot.loop
                    )

                # 3 days before end
                if (end - today).days == 3:
                    asyncio.run_coroutine_threadsafe(
                        prompt_pack_toggle(pack_key, "disable", end.strftime("%b %d")),
                        bot.loop
                    )

        except Exception as e:
            print(f"⚠️ Pack schedule loop error: {e}")

        time.sleep(86400)  # run once daily
