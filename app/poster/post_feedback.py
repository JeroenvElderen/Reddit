"""
Owner feedback helpers and feedback loop.
"""

import time, asyncio, discord
from datetime import datetime, date
from app.clients.reddit_owner import reddit_owner
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.models.state import SUBREDDIT_NAME
from app.utils.tz import current_tz
from app.config import DISCORD_DECAY_LOG_CHANNEL_ID


# =========================
# Owner Feedback Helpers
# =========================
async def send_owner_feedback(username: str, feedback_type: str):
    """Send a personalized feedback DM from OWNER account."""
    try:
        if feedback_type == "1m_feedback":
            subject = f"🌿 Feedback request from r/{SUBREDDIT_NAME}"
            body = (
                f"Hey u/{username}, you've been active in r/{SUBREDDIT_NAME} for a month now! 🌞\n\n"
                "We’d love your feedback: how do you feel about the community so far?\n"
                "Is there anything we could improve, or features you’d like to see? 💬"
            )
        elif feedback_type == "1w_rules":
            subject = f"📜 Quick check-in from r/{SUBREDDIT_NAME}"
            body = (
                f"Hey u/{username}, thanks for being with us for a week! 🌿\n\n"
                "We’re curious — what do you think about our rules and features?\n"
                "Are they clear and supportive, or do you see room for changes? 🤔"
            )
        elif feedback_type == "1w_prompts":
            subject = f"💚 Daily Prompts Check-in"
            body = (
                f"Hey u/{username}, you’ve seen our daily prompts for a week now 🌞\n\n"
                "Do you enjoy them? Would you like more variety (facts, mindfulness, trivia)?\n"
                "Your input helps us keep the community inspiring 🌿"
            )
        else:
            return

        reddit_owner.redditor(username).message(subject, body)
        print(f"📩 Owner feedback DM ({feedback_type}) sent to u/{username}")

        # Optional: log to Discord
        channel = bot.get_channel(DISCORD_DECAY_LOG_CHANNEL_ID)  # reuse decay log or create dedicated channel
        if channel:
            embed = discord.Embed(
                title="📩 Owner Feedback Sent",
                description=f"u/{username} — {feedback_type}",
                color=discord.Color.blurple(),
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"⚠️ Failed to send feedback ({feedback_type}) to u/{username}: {e}")


# =========================
# Feedback Loop (Owner Account DMs)
# =========================
def feedback_loop():
    print("🕒 Feedback loop started...")
    while True:
        try:
            today = datetime.now(current_tz()).date()
            rows = supabase.table("user_karma").select("*").execute().data or []

            for row in rows:
                name = row.get("username")
                if not name:
                    continue

                last_approved = row.get("last_approved_date")
                if not last_approved:
                    continue

                try:
                    joined = date.fromisoformat(last_approved)
                except Exception:
                    continue

                days_active = (today - joined).days

                # 1 Month Feedback
                if days_active >= 30 and not row.get("feedback_1m_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1m_feedback"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1m_sent": True}
                    ).ilike("username", name).execute()

                # 1 Week Rule Opinion
                if days_active >= 7 and not row.get("feedback_1w_rule_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1w_rules"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1w_rule_sent": True}
                    ).ilike("username", name).execute()

                # 1 Week Prompt Opinion
                if days_active >= 7 and not row.get("feedback_1w_prompt_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1w_prompts"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1w_prompt_sent": True}
                    ).ilike("username", name).execute()

        except Exception as e:
            print(f"⚠️ Feedback loop error: {e}")

        time.sleep(86400)  # run once per day
