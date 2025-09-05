"""
Approval bookkeeping: karma, flair, bonuses, streaks, achievements.
"""

import asyncio
import discord
from datetime import datetime, timedelta, date
from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.utils.tz import current_tz
from app.moderation.karma_apply import apply_karma_and_flair
from app.moderation.auto_tagger import auto_set_post_flair_if_missing
from app.moderation.counters_locations import increment_location_counter
from app.moderation.badges_pillar_award import check_pillar_badge
from app.moderation.badges_meta_award import check_meta_badge
from app.moderation.badges_seasonal_rare import check_seasonal_and_rare
from app.moderation.badges_observer_award import check_observer_badges
from app.utils.reddit_images import is_native_reddit_image
from app.config import (
    QV_ENABLED, QV_STEP_SCORE, QV_MAX_BONUS, QV_BONUS_PER_STEP,
    STREAK_ENABLED, STREAK_MIN_DAYS, STREAK_DAILY_BONUS, STREAK_MAX_BONUS_PER_DAY,
    WELCOME_ENABLED, SUBREDDIT_NAME, DISCORD_UPVOTE_LOG_CHANNEL_ID,
)


# =========================
# Approval bookkeeping
# =========================
def calc_quality_bonus_for_post(submission) -> int:
    """Award bonus karma for high upvote scores."""
    if not QV_ENABLED or not hasattr(submission, "title"):
        return 0
    try:
        score = int(getattr(submission, "score", 0) or 0)
    except Exception:
        score = 0
    steps = score // max(1, QV_STEP_SCORE)
    bonus = min(QV_MAX_BONUS, steps * QV_BONUS_PER_STEP)
    return max(0, bonus)


# =========================
# Upvote credit bookkeeping
# =========================
def credit_upvotes_for_submission(submission):
    """
    Convert net upvotes → karma for OP at a rate of 1 per 5 upvotes.
    Tracks credited_upvotes in Supabase to avoid double-paying.
    """
    try:
        post_id = submission.id
        author = submission.author
        if author is None:
            return

        name = str(author)
        title_val = submission.title[:255] if getattr(submission, "title", None) else None

        # fetch tracking row
        res = supabase.table("post_upvote_credits").select("*").eq("post_id", post_id).execute()
        row = res.data[0] if res.data else None
        credited = int(row.get("credited_upvotes", 0)) if row else 0

        # current net score (floor at 0)
        try:
            score = int(getattr(submission, "score", 0) or 0)
        except Exception:
            score = 0
        score = max(0, score)

        delta_upvotes = score - credited
        if delta_upvotes <= 0:
            # nothing new → just refresh last_checked_at and store title
            supabase.table("post_upvote_credits").upsert({
                "post_id": post_id,
                "username": name,
                "credited_upvotes": credited,
                "last_checked_at": datetime.utcnow().isoformat(),
                "post_title": title_val,
            }).execute()
            return

        # 1 karma per 5 upvotes
        award = delta_upvotes // 5
        if award <= 0:
            # not enough to reach a new multiple of 5 yet → just refresh
            supabase.table("post_upvote_credits").upsert({
                "post_id": post_id,
                "username": name,
                "credited_upvotes": credited,
                "last_checked_at": datetime.utcnow().isoformat(),
                "post_title": title_val,
            }).execute()
            return

        # grant karma
        old_k, new_k, flair = apply_karma_and_flair(name, award, allow_negative=False)

        # save new credited count (consume award*5 upvotes)
        new_credited = credited + award * 5
        supabase.table("post_upvote_credits").upsert({
            "post_id": post_id,
            "username": name,
            "credited_upvotes": new_credited,
            "last_checked_at": datetime.utcnow().isoformat(),
            "post_title": title_val,
        }).execute()

        print(f"🏅 Upvote credit: u/{name} +{award} karma for {delta_upvotes} new upvotes (credited {new_credited})")

        # optional: log to Discord channel
        try:
            channel = bot.get_channel(DISCORD_UPVOTE_LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🏅 Upvote Reward",
                    description=f"u/{name} gained **+{award}** karma from post upvotes",
                    color=discord.Color.gold()
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


# ========================
# Main approval flow
# ========================
def on_first_approval_welcome(item, author_name: str, old_karma: int):
    """Send a welcome reply if this is the user's very first approved item."""
    if not WELCOME_ENABLED or old_karma != 0:
        return
    try:
        text = (
            f"Hey u/{author_name} — welcome to r/{SUBREDDIT_NAME}! 🌞\n\n"
            "Thanks for contributing. Please remember:\n"
            "• Be respectful & follow our community rules\n"
            "• Blur faces / remove location data if needed\n"
            "• Use clear titles and context for photos\n"
            "• Try `!help` in a DM to me for commands\n\n"
            "Happy posting! 🌿"
        )
        item.reply(text)
        print(f"👋 Welcome reply posted for u/{author_name}")
    except Exception as e:
        print(f"⚠️ Welcome reply failed: {e}")


def apply_approval_points_and_flair(item, total_delta: int):
    """Apply delta karma and update flair accordingly."""
    old_k2, new_k, flair = apply_karma_and_flair(item.author, total_delta, allow_negative=False)
    return old_k2, new_k, flair


def award_achievements_once(item, name: str, row: dict):
    """Award achievements for ``item`` once, tracking by item ID in Supabase."""
    item_id = getattr(item, "id", None)
    if not item_id:
        return
    kind = "post" if hasattr(item, "title") else "comment"
    try:
        tbl = supabase.table("seen_reddit_ids")
        already = tbl.select("id").eq("id", item_id).execute()
        if already.data:
            return

        if hasattr(item, "title"):  # only posts, not comments
            increment_location_counter(item, name)

            # Increment Pillars
            title_body = (getattr(item, "title", "") + " " + getattr(item, "selftext", "")).lower()
            pillar_fields = {
                "body": "bodypositivity_posts_count",
                "travel": "travel_posts_count",
                "mind": "mindfulness_posts_count",
                "advocacy": "advocacy_posts_count",
            }
            for kw, field in pillar_fields.items():
                if kw in title_body:
                    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
                    row2 = res.data[0] if res.data else {}
                    current = int(row2.get(field, 0))
                    new_val = current + 1
                    supabase.table("user_karma").upsert({"username": name, field: new_val}).execute()
                    check_pillar_badge(name, field, new_val)

            # Meta ladder → total naturist posts
            res = supabase.table("user_karma").select("*").ilike("username", name).execute()
            row2 = res.data[0] if res.data else {}
            total = int(row2.get("naturist_total_posts", 0)) + 1
            supabase.table("user_karma").upsert({"username": name, "naturist_total_posts": total}).execute()
            check_meta_badge(name, total)

            # Seasonal (detect by month)
            month = datetime.utcnow().month
            field_map = {
                12: "posted_in_winter", 1: "posted_in_winter", 2: "posted_in_winter",
                3: "posted_in_spring", 4: "posted_in_spring", 5: "posted_in_spring",
                6: "posted_in_summer", 7: "posted_in_summer", 8: "posted_in_summer",
                9: "posted_in_autumn", 10: "posted_in_autumn", 11: "posted_in_autumn"
            }
            season_field = field_map.get(month)
            if season_field:
                supabase.table("user_karma").update({season_field: True}).ilike("username", name).execute()

            # Check Seasonal & Rare
            row2 = supabase.table("user_karma").select("*").ilike("username", name).execute().data[0]
            check_seasonal_and_rare(name, row2)

        # 🌙 Observer badges
        if row.get("last_flair") == "Quiet Observer":
            if not hasattr(item, "title"):  # comment
                comments = int(row.get("observer_comments_count", 0)) + 1
                supabase.table("user_karma").upsert({
                    "username": name,
                    "observer_comments_count": comments
                }).execute()
                row["observer_comments_count"] = comments

            # add upvotes (both posts & comments)
            try:
                score = int(getattr(item, "score", 0) or 0)
            except Exception:
                score = 0
            upvotes = int(row.get("observer_upvotes_total", 0)) + score
            supabase.table("user_karma").upsert({
                "username": name,
                "observer_upvotes_total": upvotes
            }).execute()
            row["observer_upvotes_total"] = upvotes

            check_observer_badges(name, row)

        tbl.upsert({"id": item_id, "kind": kind}).execute()
    except Exception as e:
        print(f"⚠️ Achievement ladder failed: {e}")


def apply_approval_awards(item, is_manual: bool):
    """Main entrypoint: apply karma, streaks, bonuses, achievements when a post/comment is approved.

    Auto-approved items (``is_manual`` is ``False``) should not receive karma or achievements.
    """
    author = item.author
    name = str(author)
    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
    row = res.data[0] if res.data else {}
    old_k = int(row.get("karma", 0))
    flair = row.get("last_flair", "—")

    if hasattr(item, "title"):
        try:
            auto_set_post_flair_if_missing(item)
        except Exception:
            pass

    if not is_manual:
        award_achievements_once(item, name, row)
        return old_k, old_k, flair, 0, ""

    if not is_manual:
        flair = row.get("last_flair", "—")
        try:
            if hasattr(item, "title"):
                auto_set_post_flair_if_missing(item)
        except Exception:
            pass
        return old_k, old_k, flair, 0, ""

    last_date_s = row.get("last_approved_date")
    streak_days = int(row.get("streak_days", 0))
    welcomed = bool(row.get("welcomed", False))

    # base
    if hasattr(item, "title"):
        base = 5 if is_native_reddit_image(item) else 1
    else:
        base = 1

    extras = []

    # streak update (by local date)
    today = datetime.now(current_tz()).date()
    yesterday = today - timedelta(days=1)
    last_date = None
    if last_date_s:
        try:
            last_date = date.fromisoformat(last_date_s)
        except Exception:
            last_date = None

    if last_date == today:
        pass
    elif last_date == yesterday:
        streak_days += 1
    else:
        streak_days = 1

    streak_bonus = 0
    if STREAK_ENABLED and streak_days >= STREAK_MIN_DAYS:
        streak_bonus = min(STREAK_DAILY_BONUS, STREAK_MAX_BONUS_PER_DAY)
        if streak_bonus > 0:
            extras.append(f"streak +{streak_bonus} (streak {streak_days}d)")

    # quality vote (posts only)
    qv_bonus = 0
    if hasattr(item, "title"):
        qv_bonus = calc_quality_bonus_for_post(item)
        if qv_bonus > 0:
            extras.append(f"quality +{qv_bonus} (score {getattr(item,'score',0)})")

    total_delta = base + streak_bonus + qv_bonus
    old_k2, new_k, flair = apply_approval_points_and_flair(item, total_delta)

    # write back streak + last approved date + welcomed
    try:
        supabase.table("user_karma").upsert({
            "username": name,
            "streak_days": streak_days,
            "last_approved_date": today.isoformat(),
            "welcomed": welcomed or (old_k == 0),
        }).execute()
    except Exception:
        pass

    try:
        if old_k == 0:
            on_first_approval_welcome(item, name, old_k)
    except Exception:
        pass

    award_achievements_once(item, name, row)

    return old_k2, new_k, flair, total_delta, ("; ".join(extras) if extras else "")
