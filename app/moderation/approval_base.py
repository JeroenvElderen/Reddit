"""
Base approval replies and decay warning helpers.
"""

import discord
from prawcore.exceptions import OAuthException

import app.clients.reddit_owner as owner_client
from app.clients.discord_bot import bot
from app.models.state import SUBREDDIT_NAME
from app.config import DISCORD_DECAY_LOG_CHANNEL_ID, DECAY_AFTER_DAYS
from app.moderation.karma_stats import get_last_approved_item


# =========================
# Decay Warning Helpers
# =========================
async def send_decay_warning(username: str, days_since: int, karma: int, flair: str):
    """Send a friendly personalized decay reminder from OWNER account."""
    try:
        last_text, is_post = get_last_approved_item(username)

        if last_text:
            if is_post:
                msg = (
                    f"Hey u/{username} 🌿\n\n"
                    f"It’s been {days_since} days since your post *“{last_text}”*. "
                    "We’d love to hear from you again soon! 🌞"
                )
            else:
                msg = (
                    f"Hey u/{username} 🌿\n\n"
                    f"It’s been {days_since} days since your comment *“{last_text}”*. "
                    "Your voice matters — join the conversation again! ✨"
                )
        else:
            msg = (
                f"Hey u/{username} 🌿\n\n"
                f"It’s been {days_since} days since your last activity. "
                "We’d love to see you back sharing and connecting with everyone! 💚"
            )

        try:
            owner_client.reddit_owner.redditor(username).message(
                f"🌿 A friendly nudge from r/{SUBREDDIT_NAME}", msg
            )
        except OAuthException:
            # Refresh credentials and retry once
            owner_client.reddit_owner = owner_client.create_reddit_owner()
            try:
                owner_client.reddit_owner.redditor(username).message(
                    f"🌿 A friendly nudge from r/{SUBREDDIT_NAME}", msg
                )
            except Exception as inner_e:
                print(
                    f"⚠️ Failed to send friendly reminder for {username} after refresh: {inner_e}"
                )
                return

        print(f"📩 Friendly reminder sent to u/{username}")

        # Optional: log to Discord decay channel
        channel = bot.get_channel(DISCORD_DECAY_LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🌿 Friendly Reminder Sent",
                description=f"u/{username} (inactive {days_since}d, decay in {DECAY_AFTER_DAYS - days_since}d)",
                color=discord.Color.green(),
            )
            embed.add_field(name="Current Karma", value=str(karma), inline=True)
            embed.add_field(name="Flair", value=flair, inline=True)
            if last_text:
                embed.add_field(name="Last Approved", value=last_text[:256], inline=False)
            await channel.send(embed=embed)

    except Exception as e:
        print(f"⚠️ Failed to send friendly reminder for {username}: {e}")
