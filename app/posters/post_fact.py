"""
Daily naturist fact poster.
"""

import asyncio
from datetime import datetime
from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.models.state import subreddit, flair_templates
from app.posters.gen_fact import generate_naturist_fact
from app.moderation.logs_auto import send_discord_auto_log


def post_daily_fact():
    """Post the daily naturist fact to Reddit + log to Discord."""
    today = datetime.utcnow().date().isoformat()

    # Skip if already posted today
    res = supabase.table("daily_facts").select("*").eq("date_posted", today).execute()
    if res.data:
        print("ℹ️ Fact already posted today, skipping.")
        return

    fact = generate_naturist_fact()
    title = "🌿 Naturist Fact of the Day"
    submission = subreddit.submit(title, selftext=fact)

    # ✅ Auto-approve
    try:
        submission.mod.approve()
        print("✅ Auto-approved Naturist Fact post")
    except Exception as e:
        print(f"⚠️ Could not auto-approve: {e}")

    # Log to Discord
    try:
        asyncio.run_coroutine_threadsafe(
            send_discord_auto_log(
                submission,
                old_k=0, new_k=0,
                flair="Daily Prompt",  # reuse if you want, or make "Daily Fact"
                awarded_points=0,
                extras_note="Bot daily fact post"
            ),
            bot.loop
        )
    except Exception as e:
        print(f"⚠️ Failed to log daily fact: {e}")

    # Apply flair
    daily_flair_id = flair_templates.get("Daily Prompt")
    if daily_flair_id:
        try:
            submission.flair.select(daily_flair_id)
            print("🏷️ Flair set to Daily Prompt")
        except Exception as e:
            print(f"⚠️ Flair set failed: {e}")

    print(f"📢 Posted daily fact")
