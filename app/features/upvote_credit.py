"""
Credit upvotes on submissions to user karma.
"""

import asyncio
import discord
from datetime import datetime
from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.moderation.karma_apply import apply_karma_and_flair
from app.config import DISCORD_UPVOTE_LOG_CHANNEL_ID


def credit_upvotes_for_submission(submission):
    """Credit new upvotes for a submission's author.

    Determines how many new net upvotes the submission has received
    since the last check and awards karma to the author at a rate of
    1 karma per 5 upvotes. Tracking information is stored in Supabase
    so the same upvotes are not counted twice. Optionally logs actions
    to a Discord channel.
    """
    try:
        post_id = submission.id
        author = submission.author
        if author is None:
            return

        name = str(author)
        title_val = submission.title[:255] if getattr(submission, "title", None) else None

        # Fetch or create tracking row for this post
        res = supabase.table("post_upvote_credits").select("*").eq("post_id", post_id).execute()
        row = res.data[0] if res.data else None
        credited = int(row.get("credited_upvotes", 0)) if row else 0

        # Current net score (floor at 0)
        try:
            score = int(getattr(submission, "score", 0) or 0)
        except Exception:
            score = 0
        score = max(0, score)

        delta_upvotes = score - credited
        if delta_upvotes <= 0:
            # Nothing new; just refresh metadata
            supabase.table("post_upvote_credits").upsert({
                "post_id": post_id,
                "username": name,
                "credited_upvotes": credited,
                "last_checked_at": datetime.utcnow().isoformat(),
                "post_title": title_val,
            }).execute()
            return

        # Award 1 karma per 5 net upvotes
        award = delta_upvotes // 5
        if award <= 0:
            supabase.table("post_upvote_credits").upsert({
                "post_id": post_id,
                "username": name,
                "credited_upvotes": credited,
                "last_checked_at": datetime.utcnow().isoformat(),
                "post_title": title_val,
            }).execute()
            return

        # Apply karma to the author
        old_k, new_k, flair = apply_karma_and_flair(name, award, allow_negative=False)

        new_credited = credited + award * 5
        supabase.table("post_upvote_credits").upsert({
            "post_id": post_id,
            "username": name,
            "credited_upvotes": new_credited,
            "last_checked_at": datetime.utcnow().isoformat(),
            "post_title": title_val,
        }).execute()

        print(
            f"🏅 Upvote credit: u/{name} +{award} karma for {delta_upvotes} new upvotes (credited {new_credited})"
        )

        # Optionally log to Discord channel
        try:
            channel = bot.get_channel(DISCORD_UPVOTE_LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🏅 Upvote Reward",
                    description=f"u/{name} gained **+{award}** karma from post upvotes",
                    color=discord.Color.gold(),
                )
                embed.add_field(name="Post", value=f"https://reddit.com{submission.permalink}", inline=False)
                embed.add_field(name="Upvotes credited", value=f"{new_credited}", inline=True)
                embed.add_field(name="Karma", value=f"{old_k} → {new_k}", inline=True)
                embed.add_field(name="Flair", value=flair, inline=True)
                embed.add_field(name="Title", value=title_val or "—", inline=False)
                asyncio.run_coroutine_threadsafe(channel.send(embed=embed), bot.loop)
        except Exception as e:
            print(f"⚠️ Upvote reward log failed: {e}")

    except Exception as e:
        print(f"⚠️ credit_upvotes_for_submission failed: {e}")