"""
Daily body positivity / mindfulness / trivia prompt poster.
"""

import asyncio, discord
from datetime import datetime
from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.models.state import subreddit
from app.posters.gen_body_positive import generate_body_positive
from app.moderation.logs_auto import send_discord_auto_log
from app.models.state import flair_templates


def post_daily_prompt():
    """Post the daily body positivity prompt to Reddit + log to Discord."""
    today = datetime.utcnow().date().isoformat()

    # Check if already posted today
    res = supabase.table("daily_bodypositive").select("*").eq("date_posted", today).execute()
    if res.data:
        print("ℹ️ Body positivity already posted today, skipping.")
        return

    # Always body positivity
    prompt = generate_body_positive()
    title = "💚 Body Positivity Prompt"

    submission = subreddit.submit(title, selftext=prompt)

    # ✅ Auto-approve bot’s own daily posts
    try:
        submission.mod.approve()
        print("✅ Auto-approved Daily Prompt post")
    except Exception as e:
        print(f"⚠️ Could not auto-approve Daily Prompt post: {e}")

    # Log to Discord
    try:
        asyncio.run_coroutine_threadsafe(
            send_discord_auto_log(
                submission,
                old_k=0, new_k=0,
                flair="Daily Prompt",
                awarded_points=0,
                extras_note="Bot daily body positivity post"
            ),
            bot.loop
        )
    except Exception as e:
        print(f"⚠️ Failed to log daily prompt: {e}")

    # Try to apply Daily Prompt flair
    daily_flair_id = flair_templates.get("Daily Prompt")
    if daily_flair_id:
        try:
            submission.flair.select(daily_flair_id)
            print("🏷️ Flair set to Daily Prompt")
        except Exception as e:
            print(f"⚠️ Could not set flair: {e}")
    else:
        print("ℹ️ No Daily Prompt flair ID configured, skipping flair")

    print(f"📢 Posted daily body positivity prompt")
