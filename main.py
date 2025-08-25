import os
import time
import json
import threading
import asyncio
import openai
import random
from datetime import datetime, date, timedelta, timezone, time as dtime
from urllib.parse import urlparse

import praw
import discord
from discord.ext import commands
from supabase import create_client, Client


openai.api_key = os.getenv("OPENAI_API_KEY")

# =========================
# Supabase
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# Reddit (PRAW, sync)
# =========================
# This is the bot account
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# This is the owner account
reddit_owner = praw.Reddit(
    client_id=os.getenv("OWNER_REDDIT_CLIENT_ID"),
    client_secret=os.getenv("OWNER_REDDIT_CLIENT_SECRET"),
    username=os.getenv("OWNER_REDDIT_USERNAME"),
    password=os.getenv("OWNER_REDDIT_PASSWORD"),
    user_agent=os.getenv("OWNER_REDDIT_USER_AGENT"),
)

SUBREDDIT_NAME = "PlanetNaturists"
subreddit = reddit.subreddit(SUBREDDIT_NAME)
# =========================
# bot account flair
# ========================
BOT_USERNAME = os.getenv("REDDIT_USERNAME", "").lower()
BOT_FLAIR_ID = os.getenv("BOT_FLAIR_ID", "ce269096-81b1-11f0-b51d-6ecc7a96815b")

# =========================
# Discord
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
DISCORD_DECAY_LOG_CHANNEL_ID = int(os.getenv("DISCORD_DECAY_LOG_CHANNEL_ID", "1408406356582731776"))
DISCORD_APPROVAL_LOG_CHANNEL_ID = int(os.getenv("DISCORD_APPROVAL_LOG_CHANNEL_ID", "1408406760322240572"))
DISCORD_REJECTION_LOG_CHANNEL_ID = int(os.getenv("DISCORD_REJECTION_LOG_CHANNEL_ID", "1408406824453148725"))

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# Config (ENV)
# =========================
# Night Guard + ping
TZ_NAME = os.getenv("TZ", "Europe/Dublin")
NIGHT_GUARD_ENABLED = os.getenv("NIGHT_GUARD_ENABLED", "1") == "1"
NIGHT_GUARD_WINDOW = os.getenv("NIGHT_GUARD_WINDOW", "00:00-06:00")
NIGHT_GUARD_MIN_KARMA = int(os.getenv("NIGHT_GUARD_MIN_KARMA", "1000"))
MOD_PING_ROLE_ID = int(os.getenv("MOD_PING_ROLE_ID", "0"))  # Discord role ID (optional)
MOD_PING_COOLDOWN_SEC = int(os.getenv("MOD_PING_COOLDOWN_SEC", "600"))
_last_mod_ping_ts = 0.0

# Karma decay
DECAY_ENABLED = os.getenv("DECAY_ENABLED", "1") == "1"
DECAY_AFTER_DAYS = int(os.getenv("DECAY_AFTER_DAYS", "7"))
DECAY_PER_DAY = int(os.getenv("DECAY_PER_DAY", "1"))
DECAY_RUN_HOUR = int(os.getenv("DECAY_RUN_HOUR", "3"))

# Streak bonus
STREAK_ENABLED = os.getenv("STREAK_ENABLED", "1") == "1"
STREAK_MIN_DAYS = int(os.getenv("STREAK_MIN_DAYS", "3"))
STREAK_DAILY_BONUS = int(os.getenv("STREAK_DAILY_BONUS", "1"))
STREAK_MAX_BONUS_PER_DAY = int(os.getenv("STREAK_MAX_BONUS_PER_DAY", "1"))

# Quality vote (posts only)
QV_ENABLED = os.getenv("QV_ENABLED", "1") == "1"
QV_STEP_SCORE = int(os.getenv("QV_STEP_SCORE", "25"))
QV_BONUS_PER_STEP = int(os.getenv("QV_BONUS_PER_STEP", "1"))
QV_MAX_BONUS = int(os.getenv("QV_MAX_BONUS", "5"))

# Welcome reply
WELCOME_ENABLED = os.getenv("WELCOME_ENABLED", "1") == "1"

# SLA / Priority re-posting
SLA_MINUTES = int(os.getenv("SLA_MINUTES", "5"))
SLA_PRIORITY_PREFIX = os.getenv("SLA_PRIORITY_PREFIX", "🔥 PRIORITY")

# ====== Queue ETA (NEW) ======
ETA_SAMPLE_WINDOW_MIN = int(os.getenv("ETA_SAMPLE_WINDOW_MIN", "60"))
ETA_ACTIVE_REVIEWER_TIMEOUT_MIN = int(os.getenv("ETA_ACTIVE_REVIEWER_TIMEOUT_MIN", "10"))
ETA_MIN_SEC = int(os.getenv("ETA_MIN_SEC", "60"))          # floor 1 min
ETA_MAX_SEC = int(os.getenv("ETA_MAX_SEC", "3600"))        # ceiling 60 min
ETA_DEFAULT_DECISION_SEC = int(os.getenv("ETA_DEFAULT_DECISION_SEC", "180"))  # fallback avg 3 min

# Auto-tagger (post flair) — stays OFF unless you set these
POST_FLAIR_IMAGE_ID = os.getenv("POST_FLAIR_IMAGE_ID", "")
POST_FLAIR_TEXT_ID = os.getenv("POST_FLAIR_TEXT_ID", "")
POST_FLAIR_LINK_ID = os.getenv("POST_FLAIR_LINK_ID", "")
POST_FLAIR_KEYWORDS = os.getenv("POST_FLAIR_KEYWORDS", "")


# =========================
# Rejection reasons (1–10 + extra)
# =========================
REJECTION_REASONS = {
    "1️⃣": "Rule 1: This is a naturist space, not a fetish subreddit.",
    "2️⃣": "Rule 2: Respect consent and privacy.",
    "3️⃣": "Rule 3: Nudity allowed, never sexualized.",
    "4️⃣": "Rule 4: No content involving minors.",
    "5️⃣": "Rule 5: Be kind, civil, and body-positive.",
    "6️⃣": "Rule 6: Keep it on-topic.",
    "7️⃣": "Rule 7: Tag nudity as NSFW.",
    "8️⃣": "Rule 8: No creepy or inappropriate behavior.",
    "9️⃣": "Rule 9: No advertising or promotion.",
    "🔟": "Rule 10: Be mindful when sharing personal photos.",
    "📝": "Removed because it had no meaningful addition to the post or discussion.",
    "✏️": "Custom reason (to be filled manually)",

}
# =========================
# 🌿 Naturist emoji pool for creative posts
# =========================
NATURIST_EMOJIS = [
    "🌿", "🌞", "🌊", "✨", "🍂", "❄️", "🌸", "☀️",
    "👣", "🌍", "💚", "🌴", "🏕️", "🧘", "🌳", "🏖️", "🔥"
]

def sprinkle_emojis(text: str, count: int = 3) -> str:
    """Randomly add naturist emojis to the start/end of a message."""
    chosen = random.sample(NATURIST_EMOJIS, k=min(count, len(NATURIST_EMOJIS)))
    return f"{' '.join(chosen)} {text} {' '.join(chosen)}"

# =========================
# Flair ladder + user flair templates 
# =========================
flair_ladder = [
    ("Cover Curious", 0),
    ("First Bare", 10),
    ("Skin Fresh", 50),
    ("Sun Chaser", 100),
    ("Breeze Walker", 250),
    ("Clothing Free", 500),
    ("Open Air", 1000),
    ("True Naturist", 2000),
    ("Bare Master", 5000),
    ("Naturist Legend", 10000),
]

flair_templates = {
    "Needs Growth": "75c23a86-7f6d-11f0-8745-f666d1d62ce4",
    "Cover Curious": "ae791af4-7d22-11f0-934a-2e3446070201",
    "First Bare": "bbf4d5d8-7d22-11f0-b485-d64b23d9d74f",
    "Skin Fresh": "c5be4a5e-7d22-11f0-b278-0298fe10eba2",
    "Sun Chaser": "d72ca790-7d22-11f0-a0de-a687510f7c1a",
    "Breeze Walker": "e35fc826-7d22-11f0-8742-d64b23d9d74f",
    "Clothing Free": "f01b2e02-7d22-11f0-bee0-7e43d54e1cf4",
    "Open Air": "7cfdbc2c-7dd7-11f0-9936-9e1c00b89022",
    "True Naturist": "8a5fbeb0-7dd7-11f0-9fa7-2e98a4cf4302",
    "Bare Master": "987da246-7dd7-11f0-ae7f-8206f7eb2e0a",
    "Naturist Legend": "a3f1f8fc-7dd7-11f0-b2c1-227301a06778",
    "Daily Prompt": "8b04873e-80d8-11f0-81d2-260f76f8fd83",
}

# =========================
# location flair -> supabase Mapping
# =========================
FLAIR_TO_FIELD = {
    "Beach": "beach_posts_count",
    "Lake": "lake_posts_count",
    "River": "river_posts_count",
    "Hot Spring": "hotspring_posts_count",
    "Poolside": "pool_posts_count",
    "Forest": "forest_posts_count",
    "Mountain": "mountain_posts_count",
    "Meadow": "meadow_posts_count",
    "Desert": "desert_posts_count",
    "Cave": "cave_posts_count",
    "Tropical": "tropical_posts_count",
    "Nordic / Cold": "nordic_posts_count",
    "Island": "island_posts_count",
    "Urban": "urban_posts_count",
    "Countryside": "countryside_posts_count",
    "Festival": "festival_posts_count",
    "Resort / Club": "resort_posts_count",
    "Camping": "camping_posts_count",
    "Backyard / Home": "backyard_posts_count",
    "Sauna / Spa": "sauna_posts_count",
}
# badge thresholds
BADGE_THRESHOLDS = [3, 7, 15, 30, 50]

# pillar thresholds
PILLAR_THRESHOLDS = [1, 3, 5, 10, 15, 25, 40, 60, 80, 100]

# ultimate ladder
META_THRESHOLDS = [10, 25, 50, 100, 150, 200, 300, 400, 500, 1000]
META_TITLES = [
    "Curious Explorer 🌱",
    "Bare Adventurer 👣",
    "Naturist Voice 🗣️",
    "Nature Friend 🌿",
    "Community Root 🌳",
    "Sun Chaser 🌞",
    "Open Spirit ✨",
    "Earth Child 🌍",
    "Naturist Sage 🧘",
    "Naturist Legend 👑"
]

def badge_level_label(level: int, max_level: int) -> str:
    """Return Lv.MAX if level is the last one, otherwise Lv.{n}"""
    return "Lv.MAX" if level == max_level else f"Lv.{level}"

# =========================
# State
# =========================
# pending_reviews[msg_id] = {"item": praw obj, "created_ts": float, "last_escalated_ts": float, "level": int}
pending_reviews = {}
seen_ids = set()

# Queue ETA state
decision_durations = []   # list[(ts, duration_sec)]
mod_activity = {}         # {discord_user_id: last_action_ts}

# =========================
# Utilities
# =========================
try:
    from zoneinfo import ZoneInfo
except Exception:
    from backports.zoneinfo import ZoneInfo

def current_tz() -> ZoneInfo:
    return ZoneInfo(TZ_NAME)

def _parse_window(s: str):
    a, b = s.split("-")
    h1, m1 = map(int, a.split(":"))
    h2, m2 = map(int, b.split(":"))
    return dtime(h1, m1), dtime(h2, m2)

def in_night_guard_window(now: datetime) -> bool:
    if not NIGHT_GUARD_ENABLED:
        return False
    start_t, end_t = _parse_window(NIGHT_GUARD_WINDOW)
    local_t = now.timetz()
    return start_t <= local_t.replace(tzinfo=None) <= end_t

def get_flair_for_karma(karma: int) -> str:
    if karma < 0:
        return "Needs Growth"   # 👈 use your special flair
    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked


def apply_karma_and_flair(user_or_name, delta: int, allow_negative: bool):
    """Apply delta to karma (floor at 0 if allow_negative=False) and update user flair."""
    if user_or_name is None:
        return 0, 0, "Cover Curious"

    name = str(user_or_name).lower()

    # 🔒 Special case: bot account always keeps fixed flair
    if name == BOT_USERNAME:
        try:
            subreddit.flair.set(redditor=name, flair_template_id=BOT_FLAIR_ID)
            print(f"🤖 Bot account flair forced to ID {BOT_FLAIR_ID}")
        except Exception as e:
            print(f"⚠️ Failed to set bot flair: {e}")
        return 0, 0, "Bot"

    # --- Normal user flow ---
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    row = res.data[0] if res.data else {}
    old = int(row.get("karma", 0))
    new = old + delta
    if not allow_negative:
        new = max(0, new)
    flair = get_flair_for_karma(new)
    supabase.table("user_karma").upsert({"username": name, "karma": new, "last_flair": flair}).execute()
    flair_id = flair_templates.get(flair)
    if flair_id:
        subreddit.flair.set(redditor=name, flair_template_id=flair_id)
        print(f"🏷️ Flair set for {name} → {flair} ({new} karma)")
    return old, new, flair


# =========================
# get last approved item
# =========================

def get_last_approved_item(username: str):
    """Return (text, is_post) of the last approved post/comment, or (None, None)."""
    try:
        redditor = reddit.redditor(username)  # use bot session to check history

        # Check posts first
        for sub in redditor.submissions.new(limit=20):
            if getattr(sub, "approved", False):
                return sub.title, True

        # If no approved posts, check comments
        for com in redditor.comments.new(limit=20):
            if getattr(com, "approved", False):
                snippet = com.body.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                return snippet, False
    except Exception as e:
        print(f"⚠️ Could not fetch last approved item for {username}: {e}")

    return None, None

# =========================
# Location flair counters + badges
# =========================
def increment_location_counter(submission, author_name: str):
    """Increment Supabase counter based on post flair."""
    flair = submission.link_flair_text
    if not flair or flair not in FLAIR_TO_FIELD:
        return

    field = FLAIR_TO_FIELD[flair]
    try:
        res = supabase.table("user_karma").select("*").eq("username", author_name).execute()
        row = res.data[0] if res.data else {}
        current = int(row.get(field, 0))
        new_val = current + 1

        supabase.table("user_karma").upsert({
            "username": author_name,
            field: new_val
        }).execute()

        print(f"🏷️ Incremented {field} for u/{author_name} → {new_val}")
        check_and_award_badge(author_name, field, new_val)

    except Exception as e:
        print(f"⚠️ Failed to increment location counter: {e}")


def check_and_award_badge(username: str, field: str, count: int):
    """Check if a user unlocked a new badge level."""
    level = sum(1 for t in BADGE_THRESHOLDS if count >= t)
    if level == 0:
        return

    # Example: beach_posts_count → Beach Lv.2
    base = field.replace("_posts_count", "").replace("_", " ").title()
    badge_name = f"{base} {badge_level_label(level, len(BADGE_THRESHOLDS))}"

    try:
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": badge_name,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌟 Badge unlocked: {badge_name} for u/{username}")

        # Optional: DM user from owner account
        try:
            reddit_owner.redditor(username).message(
                "🌟 New Naturist Achievement!",
                f"Congrats u/{username}! You just reached **{badge_name}** 🏆\n\n"
                f"Keep exploring naturism and sharing your journey 🌞"
            )
        except Exception as e:
            print(f"⚠️ Could not DM badge to {username}: {e}")

    except Exception as e:
        print(f"⚠️ Could not save badge for {username}: {e}")

def check_pillar_badge(username: str, field: str, count: int):
    """Check 10-level naturist pillar ladders (body positivity, travel, etc)."""
    level = sum(1 for t in PILLAR_THRESHOLDS if count >= t)
    if level == 0:
        return
    base = field.replace("_posts_count", "").replace("_", " ").title()
    badge_name = f"{base} {badge_level_label(level, len(PILLAR_THRESHOLDS))}"
    supabase.table("user_badges").upsert({
        "username": username,
        "badge": badge_name,
        "unlocked_on": datetime.utcnow().isoformat()
    }).execute()
    print(f"🌟 Pillar badge unlocked: {badge_name} for u/{username}")

# =========================
# Meta badge, seasonal, rare badges
# =========================
def check_meta_badge(username: str, total_count: int):
    """Check 10-level ultimate naturist ladder (meta)."""
    level = sum(1 for t in META_THRESHOLDS if total_count >= t)
    if level == 0:
        return
    badge_name = f"{META_TITLES[level - 1]} {badge_level_label(level, len(META_THRESHOLDS))}"
    supabase.table("user_badges").upsert({
        "username": username,
        "badge": badge_name,
        "unlocked_on": datetime.utcnow().isoformat()
    }).execute()
    print(f"👑 Meta badge unlocked: {badge_name} for u/{username}")


def check_seasonal_and_rare(username: str, row: dict):
    """Check seasonal & rare single-unlock badges."""
    # Seasonal
    if all([row.get("posted_in_spring"), row.get("posted_in_summer"),
            row.get("posted_in_autumn"), row.get("posted_in_winter")]):
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": "Seasonal Naturist 🍂❄️🌸☀️",
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌟 Seasonal badge unlocked for u/{username}")

    # Rare
    if row.get("festivals_attended", 0) >= 1:
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": "Festival Free Spirit 🎶",
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🎶 Festival badge unlocked for u/{username}")

    if row.get("countries_posted", 0) >= 5:
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": "Naturist Traveler 🌍",
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌍 Traveler badge unlocked for u/{username}")

# =========================
# Weekly achievements digest formatter
# =========================
def format_weekly_achievements(rows):
    if not rows:
        return None

    locations, pillars, meta, rare = [], [], [], []

    for row in rows:
        u = row["username"]
        badge = row["badge"]

        # Format line
        line = f"• u/{u} → {badge}"

        # Categorize based on badge text
        if any(loc in badge for loc in [
            "Beach","Forest","Lake","Mountain","Meadow","River",
            "Pool","Backyard","Camping","Sauna","Resort","Island",
            "Countryside","Cave","Tropical","Nordic","Festival"
        ]):
            locations.append(line)
        elif "Lv." in badge and not any(meta_kw in badge for meta_kw in [
            "Seed","Explorer","Adventurer","Voice","Friend","Root",
            "Chaser","Spirit","Child","Legend"
        ]):
            pillars.append(line)
        elif any(meta_kw in badge for meta_kw in [
            "Seed","Explorer","Adventurer","Voice","Friend","Root",
            "Chaser","Spirit","Child","Legend"
        ]):
            meta.append(line)
        else:
            rare.append(line)

    parts = []
    # Big Header
    parts.append("🌟🌿🌞🌿🌟\n✨ Weekly Naturist Achievements ✨\n🌟🌿🌞🌿🌟\n")

    if locations:
        parts.append("🏖️ **Location Achievements**\n" + "\n".join(locations) + "\n\n🌿🌿🌿🌿🌿")
    if pillars:
        parts.append("🧘 **Pillar Progress**\n" + "\n".join(pillars) + "\n\n🌿🌿🌿🌿🌿")
    if meta:
        parts.append("👑 **Meta Ladder**\n" + "\n".join(meta) + "\n\n🌿🌿🌿🌿🌿")
    if rare:
        parts.append("🎉 **Special Unlocks**\n" + "\n".join(rare) + "\n\n🌿🌿🌿🌿🌿")

    parts.append("🌞💚 Keep shining, sharing, and celebrating naturism! ✨🌿")

    return "\n\n".join(parts)


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

        reddit_owner.redditor(username).message(
            f"🌿 A friendly nudge from r/{SUBREDDIT_NAME}", msg
        )
        print(f"📩 Friendly reminder sent to u/{username}")

        # Optional: still log to Discord decay channel
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

        # Optional: log to Discord for mods
        channel = bot.get_channel(DISCORD_DECAY_LOG_CHANNEL_ID)  # reuse decay log or make a new FEEDBACK log channel
        if channel:
            embed = discord.Embed(
                title="📩 Owner Feedback Sent",
                description=f"u/{username} — {feedback_type}",
                color=discord.Color.blurple(),
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"⚠️ Failed to send feedback ({feedback_type}) to u/{username}: {e}")

# ---------- Language hinting ----------
EN_STOPWORDS = {
    "the","be","to","of","and","a","in","that","have","i","it","for","not",
    "on","with","he","as","you","do","at","this","but","his","by","from","we",
    "say","her","she","or","an","will","my","one","all","would","there","their"
}
def likely_english(text: str) -> bool:
    if not text:
        return True
    t = text.lower()
    letters = sum(ch.isalpha() for ch in t)
    ascii_letters = sum(('a' <= ch <= 'z') for ch in t)
    ratio = (ascii_letters / max(1, letters))
    sw_hits = sum(1 for w in EN_STOPWORDS if f" {w} " in f" {t} ")
    score = ratio + 0.05 * sw_hits
    return score >= 0.6

def item_text(item) -> str:
    if hasattr(item, "title"):
        return f"{item.title}\n\n{item.selftext or ''}"
    return item.body or ""

# ---------- Image helpers ----------
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".webp", ".bmp", ".tiff", ".svg")
REDDIT_IMAGE_HOSTS = {"i.redd.it", "i.reddituploads.com"}

def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def submission_has_any_image(sub) -> bool:
    try:
        if getattr(sub, "is_gallery", False):
            return True
        url = (getattr(sub, "url", "") or "").lower()
        if any(url.endswith(ext) for ext in IMAGE_EXTS):
            return True
        if getattr(sub, "post_hint", None) == "image":
            return True
        preview = getattr(sub, "preview", None)
        if isinstance(preview, dict) and preview.get("images"):
            return True
    except Exception:
        pass
    return False

def is_native_reddit_image(sub) -> bool:
    if not hasattr(sub, "title"):
        return False
    if getattr(sub, "is_gallery", False):
        md = getattr(sub, "media_metadata", {}) or {}
        for v in md.values():
            if v.get("e") == "Image":
                src = v.get("s", {}) or {}
                u = src.get("u") or src.get("gif") or ""
                if any(_host(u).endswith(h) for h in REDDIT_IMAGE_HOSTS):
                    return True
        return False
    url = (getattr(sub, "url", "") or "")
    if getattr(sub, "post_hint", None) == "image" and url:
        if any(_host(url).endswith(h) for h in REDDIT_IMAGE_HOSTS):
            return True
    preview = getattr(sub, "preview", None)
    if isinstance(preview, dict):
        imgs = preview.get("images") or []
        for img in imgs:
            src_url = (img.get("source", {}) or {}).get("url", "")
            if any(_host(src_url).endswith(h) for h in REDDIT_IMAGE_HOSTS):
                return True
    return False

def image_flag_label(sub) -> str:
    if not hasattr(sub, "title"):
        return "N/A"
    if is_native_reddit_image(sub):
        return "Native"
    if submission_has_any_image(sub):
        return "External"
    return "No"

# ---------- Shadow flags ----------
def get_shadow_flag(username: str) -> str | None:
    try:
        res = supabase.table("shadow_flags").select("note").eq("username", username).execute()
        if res.data:
            note = (res.data[0].get("note") or "").strip()
            return note or None
    except Exception:
        pass
    return None

# ========================
# User stats fetcher
# =========================
def get_user_stats(username: str):
    """Fetch stats for a given user from Supabase."""
    try:
        res = supabase.table("user_karma").select("*").eq("username", username).execute()
        if not res.data:
            return None
        row = res.data[0]
        return {
            "karma": int(row.get("karma", 0)),
            "flair": row.get("last_flair", "Needs Growth"),
            "streak": int(row.get("streak_days", 0)),
            "last_post": row.get("last_approved_date"),
        }
    except Exception as e:
        print(f"⚠️ Stats lookup failed for {username}: {e}")
        return None


# =========================
# Reddit DM Commands
# =========================

def cmd_stats(author: str, message):
    stats = get_user_stats(author)
    if not stats:
        message.reply(f"🌿 Hey u/{author}, I couldn’t find any stats yet. Try posting or commenting!")
        return
    message.reply(
        f"🌞 **Your r/{SUBREDDIT_NAME} Stats** 🌿\n\n"
        f"- Karma: **{stats['karma']}**\n"
        f"- Flair: **{stats['flair']}**\n"
        f"- Streak: **{stats['streak']} days**\n"
        f"- Last approved post: **{stats['last_post'] or '—'}**\n\n"
        "Keep contributing to grow your naturist flair and karma! 💚"
    )

def cmd_flairlist(author: str, message):
    flairs = "\n".join([f"{f} — {k} karma" for f, k in flair_ladder])
    message.reply("🏷️ **Flair Ladder** 🌿\n\n" + flairs)

def cmd_rules(author: str, message):
    rules_text = "\n".join([f"{emoji} {text}" for emoji, text in REJECTION_REASONS.items()])
    message.reply(f"📜 **r/{SUBREDDIT_NAME} Rules**\n\n{rules_text}")

def cmd_decay(author: str, message):
    stats = get_user_stats(author)
    if not stats:
        message.reply("🌿 No activity found yet.")
        return
    from datetime import date
    today = date.today()
    if stats["last_post"]:
        try:
            last_date = date.fromisoformat(stats["last_post"])
            since = (today - last_date).days
        except Exception:
            since = None
    else:
        since = None

    if since is None:
        message.reply("🍂 No recent posts found — you might be at risk of decay if inactive.")
    else:
        days_left = max(0, DECAY_AFTER_DAYS - since)
        message.reply(
            f"🍂 **Decay Check**\n\n"
            f"Last activity: {since} days ago\n"
            f"Decay starts after **{DECAY_AFTER_DAYS} days**.\n"
            f"You have **{days_left} days** before decay begins."
        )

def cmd_top(author: str, message):
    posts = list(subreddit.top(time_filter="week", limit=5))
    lines = [
        f"{i+1}. [{p.title}](https://reddit.com{p.permalink}) — {p.score} upvotes"
        for i, p in enumerate(posts)
    ]
    message.reply("🌞 **Top Posts This Week** 🌿\n\n" + "\n".join(lines))

def cmd_safety(author: str, message):
    message.reply(
        "🛡 **Safety Tips for Naturists** 🌿\n\n"
        "- Blur faces / remove location data\n"
        "- Respect consent & privacy\n"
        "- Tag NSFW correctly\n"
        "- Report creepy or unsafe behavior to mods"
    )

def cmd_help(author: str, message):
    commands = {
        "!stats": "See your karma, flair, streak",
        "!flairlist": "View all flair levels",
        "!rules": "Read subreddit rules",
        "!decay": "Check if you’re close to decay",
        "!top": "See this week’s top posts",
        "!safety": "Naturist safety tips",
        "!help": "Show this menu",
    }
    message.reply(
        "🤖 **Available Commands** 🌿\n\n"
        + "\n".join([f"- {c} → {desc}" for c, desc in commands.items()])
        + "\n\nType any command in DM (e.g., `!stats`)."
    )

# Map of available commands
COMMANDS = {
    "!stats": cmd_stats,
    "!flairlist": cmd_flairlist,
    "!rules": cmd_rules,
    "!decay": cmd_decay,
    "!top": cmd_top,
    "!safety": cmd_safety,
    "!help": cmd_help,
}

# Dispatcher loop for DM commands
def reddit_dm_polling():
    print("📩 Reddit DM polling started...")
    for message in reddit.inbox.stream(skip_existing=True):
        try:
            if not isinstance(message, praw.models.Message):
                continue
            body = message.body.strip().lower()
            author = str(message.author)

            if body.startswith("!"):
                command = body.split()[0]  # first word
                handler = COMMANDS.get(command)
                if handler:
                    handler(author, message)
                    print(f"✅ Executed {command} for u/{author}")
                else:
                    message.reply(
                        f"⚠️ Unknown command `{command}`.\n"
                        f"Type `!help` to see available commands."
                    )
                    print(f"⚠️ Unknown command {command} from u/{author}")

        except Exception as e:
            print(f"⚠️ Error processing DM: {e}")


# =========================
# Pending reviews persistence (Supabase)
# =========================
def save_pending_review(msg_id: int, item, level: int):
    try:
        supabase.table("pending_reviews").upsert({
            "msg_id": msg_id,
            "item_id": item.id,
            "is_submission": hasattr(item, "title"),
            "created_ts": datetime.utcnow().isoformat(),
            "level": level,
        }).execute()
        print(f"💾 Saved pending review {msg_id} for {item.id}")
    except Exception as e:
        print(f"⚠️ Failed to save pending review {msg_id}: {e}")

def delete_pending_review(msg_id: int):
    try:
        supabase.table("pending_reviews").delete().eq("msg_id", msg_id).execute()
        print(f"🗑️ Deleted pending review {msg_id}")
    except Exception as e:
        print(f"⚠️ Failed to delete pending review {msg_id}: {e}")

def restore_pending_reviews():
    rows = supabase.table("pending_reviews").select("*").execute().data or []
    for row in rows:
        try:
            # Load the original item
            if row["is_submission"]:
                item = reddit.submission(id=row["item_id"])
            else:
                item = reddit.comment(id=row["item_id"])

            # ✅ Skip if already approved/removed/banned
            if already_moderated(item):
                print(f"⏩ Skipping restore for {row['item_id']} (already moderated)")
                delete_pending_review(row["msg_id"])
                continue

            # Delete the old msg_id record (since Discord card is gone)
            delete_pending_review(row["msg_id"])

            # Re-post with RESTORED marker
            asyncio.run_coroutine_threadsafe(
                send_discord_approval(
                    item,
                    lang_label="English",
                    note="🔴 Restored after bot restart",
                    priority_level=row.get("level", 0)
                ),
                bot.loop
            )

            print(f"🔴 Restored card sent to Discord for u/{item.author} (level={row.get('level',0)})")

        except Exception as e:
            print(f"⚠️ Could not restore review {row.get('msg_id')}: {e}")
            
    # ---------- OpenAI Daily Prompt Generators ----------
def generate_trivia():
    """Generate a unique trivia question and store it in Supabase."""
    try:
        for _ in range(5):  # try up to 5 times to avoid duplicates
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a trivia generator for a naturist Reddit community. "
                            "Always create varied and engaging questions: true/false, "
                            "multiple choice, or open-ended. Cover history, culture, "
                            "environment, health, famous naturist places, and body positivity. "
                            "Use emojis naturally. Never repeat previous ones."
                        )
                    },
                    {"role": "user", "content": "Write one unique naturist trivia question now."}
                ],
                max_tokens=100
            )
            question = resp.choices[0].message["content"].strip()

            # Check if already exists
            res = supabase.table("daily_trivia").select("id").eq("question", question).execute()
            if not res.data:
                # Save new question
                supabase.table("daily_trivia").insert({
                    "date_posted": datetime.now().date().isoformat(),
                    "question": question
                }).execute()
                return question

        # Fallback if all retries were duplicates
        return "🌿 In which decade did modern naturism first gain popularity in Europe?"

    except Exception as e:
        print(f"⚠️ Trivia generation failed: {e}")
        return "🌞 True or False: Naturism encourages respect for both people and nature."
        
def generate_body_positive():
    """Generate a longer uplifting body positivity message (2–5 sentences) with emojis."""
    try:
        for _ in range(5):
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a naturist body positivity coach. "
                            "Always write between 2 and 5 sentences. "
                            "Celebrate natural bodies, diversity, confidence, and freedom. "
                            "Use emojis like 🌞🌿🌊✨🌸💚 naturally throughout the message. "
                            "Each message must feel fresh, supportive, and uplifting. "
                            "Do not repeat previous prompts."
                        )
                    },
                    {"role": "user", "content": "Write one body positivity message for naturists."}
                ],
                max_tokens=200
            )
            message = resp.choices[0].message["content"].strip()

            # Check if already exists
            res = supabase.table("daily_bodypositive").select("id").eq("message", message).execute()
            if not res.data:
                # Save new message
                supabase.table("daily_bodypositive").insert({
                    "date_posted": datetime.now().date().isoformat(),
                    "message": message
                }).execute()
                return message

        # Fallback
        return "💚 Every body is unique and beautiful 🌿✨. Embrace your natural self with pride and confidence 🌞🌸🌊."

    except Exception as e:
        print(f"⚠️ Body-positive generation failed: {e}")
        return "🌞 Remember: your body is not something to fix — it's something to celebrate 🌿💚✨."
        
def generate_mindfulness():
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a meditation guide for naturists."},
                {"role": "user", "content": "Write one naturist mindfulness or meditation prompt."}
            ],
            max_tokens=60
        )
        return resp.choices[0].message["content"].strip()
    except Exception as e:
        print(f"⚠️ Mindfulness generation failed: {e}")
        return "Take a moment to feel the breeze on your skin and breathe deeply."

def generate_naturist_fact():
    """Generate a longer naturist fact (up to 5 sentences, with emojis)."""
    try:
        for _ in range(5):  # retry a few times if duplicate
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a naturist historian and educator. "
                            "Write one naturist-related fact in 2–5 sentences. "
                            "Facts can include history, culture, health, famous naturist places, or environmental aspects. "
                            "Always weave in emojis naturally (🌿🌞🌊✨💚). "
                            "Make it sound friendly and engaging for a naturist community. "
                            "Avoid repeating previous facts."
                        )
                    },
                    {"role": "user", "content": "Give one unique naturist fact now."}
                ],
                max_tokens=200
            )
            fact = resp.choices[0].message["content"].strip()

            # Check if fact already exists
            res = supabase.table("daily_facts").select("id").eq("fact", fact).execute()
            if not res.data:
                supabase.table("daily_facts").insert({
                    "date_posted": datetime.now().date().isoformat(),
                    "fact": fact
                }).execute()
                return fact

        # fallback if duplicates
        return "🌞 Did you know? Naturism has deep roots in early 20th century Europe, promoting health, freedom, and a closer bond with nature 🌿✨."

    except Exception as e:
        print(f"⚠️ Fact generation failed: {e}")
        return "🌿 Naturism celebrates respect for the earth, body positivity, and living freely under the sun 🌞."
        
# ---------- About snapshot ----------
def about_user_block(name: str):
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    sub_karma = int(res.data[0]["karma"]) if res.data else 0
    try:
        rd = reddit.redditor(name)
        created = getattr(rd, "created_utc", None)
        days = int((datetime.now(timezone.utc).timestamp() - created) / 86400) if created else "—"
    except Exception:
        days = "—"
    return sub_karma, days

# ---------- Moderation checks ----------
def already_moderated(item) -> bool:
    if getattr(item, "approved_by", None):
        return True
    if getattr(item, "removed_by_category", None) is not None:
        return True
    if getattr(item, "banned_by", None):
        return True
    if getattr(item, "author", None) is None:
        return True
    return False

# =========================
# Auto-tagger helpers (OFF unless envs are set)
# =========================
def parse_keyword_map(raw: str) -> dict[str, str]:
    out = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        k, v = pair.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out

KEYWORD_MAP = parse_keyword_map(POST_FLAIR_KEYWORDS)

def auto_set_post_flair_if_missing(submission):
    if not hasattr(submission, "title"):
        return
    if getattr(submission, "link_flair_text", None) or getattr(submission, "link_flair_template_id", None):
        return
    try:
        title = (submission.title or "").lower()
        body = (submission.selftext or "").lower()
        for kw, tmpl in KEYWORD_MAP.items():
            if kw in title or kw in body:
                if tmpl:
                    submission.flair.select(tmpl)
                    print(f"🏷️ Post flair (keyword '{kw}') set via template {tmpl}")
                    return
        if (POST_FLAIR_IMAGE_ID and (is_native_reddit_image(submission) or submission_has_any_image(submission))):
            submission.flair.select(POST_FLAIR_IMAGE_ID); print(f"🏷️ Post flair (image) set via template {POST_FLAIR_IMAGE_ID}")
        elif POST_FLAIR_TEXT_ID and body.strip():
            submission.flair.select(POST_FLAIR_TEXT_ID);  print(f"🏷️ Post flair (text) set via template {POST_FLAIR_TEXT_ID}")
        elif POST_FLAIR_LINK_ID:
            submission.flair.select(POST_FLAIR_LINK_ID);  print(f"🏷️ Post flair (link) set via template {POST_FLAIR_LINK_ID}")
    except Exception as e:
        print(f"⚠️ Post flair set failed: {e}")

# =========================
# Queue ETA helpers (NEW)
# =========================
def _prune_decision_samples(now_ts: float):
    cutoff = now_ts - ETA_SAMPLE_WINDOW_MIN * 60
    # keep only recent samples
    while decision_durations and decision_durations[0][0] < cutoff:
        decision_durations.pop(0)

def _avg_decision_sec(now_ts: float) -> float:
    _prune_decision_samples(now_ts)
    if not decision_durations:
        return float(ETA_DEFAULT_DECISION_SEC)
    total = sum(d for _, d in decision_durations)
    return max(1.0, total / len(decision_durations))

def _active_reviewers(now_ts: float) -> int:
    timeout = ETA_ACTIVE_REVIEWER_TIMEOUT_MIN * 60
    return sum(1 for ts in mod_activity.values() if now_ts - ts <= timeout) or 1

def _fmt_eta_band(low_sec: int, high_sec: int) -> str:
    def f(s):
        if s >= 3600:
            h = int(round(s / 3600.0))
            return f"~{h}h"
        m = max(1, int(round(s / 60.0)))
        return f"~{m}m"
    return f"{f(low_sec)}–{f(high_sec)}"

def compute_eta_text(pending_count: int) -> str:
    now_ts = time.time()
    avg = _avg_decision_sec(now_ts)
    act = _active_reviewers(now_ts)
    raw = avg * max(1, pending_count) / max(1, act)
    raw = int(min(max(raw, ETA_MIN_SEC), ETA_MAX_SEC))
    low = int(max(ETA_MIN_SEC, raw * 0.8))
    high = int(min(ETA_MAX_SEC, raw * 1.25))
    return _fmt_eta_band(low, high)

def record_mod_decision(created_ts: float, discord_user_id: int):
    now_ts = time.time()
    duration = max(1.0, now_ts - float(created_ts or now_ts))
    decision_durations.append((now_ts, duration))
    mod_activity[discord_user_id] = now_ts

# =========================
# Discord builders & actions
# =========================
async def _lock_and_delete_message(msg: discord.Message):
    """Decision lock: mark as LOCKED, clear reactions, then delete after a short delay."""
    try:
        embed = msg.embeds[0] if msg.embeds else None
        if embed:
            if embed.title and "🔒" not in embed.title:
                embed.title = f"🔒 {embed.title} (LOCKED)"
            embed.color = discord.Color.dark_grey()
            await msg.edit(embed=embed)
        await msg.clear_reactions()
    except Exception:
        pass
    await asyncio.sleep(2)
    try:
        await msg.delete()
    except Exception:
        pass

async def send_discord_approval(item, lang_label=None, note=None, night_guard_ping=False, priority_level:int=0):
    """Send item to Discord for manual review; optional Night Guard ping; supports PRIORITY levels + ETA."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("⚠️ Discord channel not found")
        return

    author = str(item.author)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    if hasattr(item, "title"):
        content = f"**{item.title}**\n\n{item.selftext or ''}"
        item_type = "Post"
        img_label = image_flag_label(item)
    else:
        content = item.body or ""
        item_type = "Comment"
        img_label = "N/A"

    # === Title prefix handling ===
    title_prefix = f"{SLA_PRIORITY_PREFIX} (L{priority_level}) · " if priority_level > 0 else ""
    if note and "Restored" in note:
        title_prefix = "🔴 (RESTORED) · " + title_prefix

    embed = discord.Embed(
        title=f"{title_prefix}🧾 {item_type} Pending Review",
        description=(content[:4000] + ("... (truncated)" if len(content) > 4000 else "")),
        color=discord.Color.orange() if priority_level == 0 else discord.Color.red(),
    )
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    if lang_label:
        embed.add_field(name="Language", value=lang_label, inline=True)
    if note:
        embed.add_field(name="Note", value=note, inline=False)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    # === Rules overview ===
    rules_overview = "\n".join([f"{emoji} {text}" for emoji, text in REJECTION_REASONS.items()])
    embed.add_field(name="Rules Overview", value=rules_overview[:1024], inline=False)

    # === ETA footer (NEW) ===
    eta_text = compute_eta_text(pending_count=len(pending_reviews) + 1)
    embed.set_footer(text=f"Queue ETA: {eta_text}")

    mention = ""
    if night_guard_ping and MOD_PING_ROLE_ID:
        global _last_mod_ping_ts
        now = time.time()
        if now - _last_mod_ping_ts >= MOD_PING_COOLDOWN_SEC:
            mention = f"<@&{MOD_PING_ROLE_ID}> "
            _last_mod_ping_ts = now

    msg = await channel.send(content=mention.strip() or None, embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    pending_reviews[msg.id] = {
        "item": item,
        "created_ts": time.time() if priority_level == 0 else (time.time() - SLA_MINUTES * 60 * priority_level),
        "last_escalated_ts": time.time(),
        "level": priority_level,
    }
    save_pending_review(msg.id, item, priority_level)
    print(f"📨 Sent {item_type} by u/{author} to Discord (priority={priority_level}, ETA={eta_text}, night_ping={bool(mention)})")
    
async def send_discord_auto_log(item, old_k, new_k, flair, awarded_points, extras_note=""):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return
    
    author = str(item.author)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)

    embed = discord.Embed(
        title=f"✅ Auto-approved {item_type}",
        description=(content[:1000] + ("... (truncated)" if len(content) > 1000 else "")),
        color=discord.Color.green(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k}  (+{awarded_points})", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    if extras_note:
        embed.add_field(name="Notes", value=extras_note, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)
    await channel.send(embed=embed)


async def log_approval(item, old_k: int, new_k: int, flair: str, note: str, extras: str = ""):
    """Log full approval info to the approval log channel."""
    channel = bot.get_channel(DISCORD_APPROVAL_LOG_CHANNEL_ID)
    if not channel:
        return

    author = str(item.author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    embed = discord.Embed(
        title=f"✅ Approved {item_type}",
        description=(content[:1500] + ("... (truncated)" if len(content) > 1500 else "")),
        color=discord.Color.green(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k} {note}", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    if extras:
        embed.add_field(name="Notes", value=extras, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    await channel.send(embed=embed)


async def log_rejection(item, old_k: int, new_k: int, flair: str, reason_text: str):
    """Log full rejection info (with reason) to the rejection log channel."""
    channel = bot.get_channel(DISCORD_REJECTION_LOG_CHANNEL_ID)
    if not channel:
        return

    author = str(item.author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    embed = discord.Embed(
        title=f"❌ Rejected {item_type}",
        description=(content[:1500] + ("... (truncated)" if len(content) > 1500 else "")),
        color=discord.Color.red(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Reason", value=reason_text, inline=False)   # 👈 NEW
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k} (−1)", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    await channel.send(embed=embed)

# =========================
# Approval bookkeeping
# =========================
def calc_quality_bonus_for_post(submission) -> int:
    if not QV_ENABLED or not hasattr(submission, "title"):
        return 0
    try:
        score = int(getattr(submission, "score", 0) or 0)
    except Exception:
        score = 0
    steps = score // max(1, QV_STEP_SCORE)
    bonus = min(QV_MAX_BONUS, steps * QV_BONUS_PER_STEP)
    return max(0, bonus)

def on_first_approval_welcome(item, author_name: str, old_karma: int):
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
    old_k2, new_k, flair = apply_karma_and_flair(item.author, total_delta, allow_negative=False)
    return old_k2, new_k, flair

def apply_approval_awards(item, is_manual: bool):
    author = item.author
    name = str(author)
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    row = res.data[0] if res.data else {}
    old_k = int(row.get("karma", 0))
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

    # optional auto-tagger (off unless envs set)
    try:
        if hasattr(item, "title"):
            auto_set_post_flair_if_missing(item)
    except Exception:
        pass

    try:
        if hasattr(item, "title"):  # only posts, not comments
            increment_location_counter(item, name)

            # Increment Pillars (simple keyword-based example)
            title_body = (getattr(item, "title", "") + " " + getattr(item, "selftext", "")).lower()
            pillar_fields = {
                "body": "bodypositivity_posts_count",
                "travel": "travel_posts_count",
                "mind": "mindfulness_posts_count",
                "advocacy": "advocacy_posts_count",
            }
            for kw, field in pillar_fields.items():
                if kw in title_body:
                    res = supabase.table("user_karma").select("*").eq("username", name).execute()
                    row = res.data[0] if res.data else {}
                    current = int(row.get(field, 0))
                    new_val = current + 1
                    supabase.table("user_karma").upsert({"username": name, field: new_val}).execute()
                    check_pillar_badge(name, field, new_val)

            # Meta ladder → total naturist posts
            res = supabase.table("user_karma").select("*").eq("username", name).execute()
            row = res.data[0] if res.data else {}
            total = int(row.get("naturist_total_posts", 0)) + 1
            supabase.table("user_karma").upsert({"username": name, "naturist_total_posts": total}).execute()
            check_meta_badge(name, total)

            # Seasonal (detect by post flair or month)
            month = datetime.utcnow().month
            field_map = {12: "posted_in_winter", 1: "posted_in_winter", 2: "posted_in_winter",
                         3: "posted_in_spring", 4: "posted_in_spring", 5: "posted_in_spring",
                         6: "posted_in_summer", 7: "posted_in_summer", 8: "posted_in_summer",
                         9: "posted_in_autumn", 10: "posted_in_autumn", 11: "posted_in_autumn"}
            season_field = field_map.get(month)
            if season_field:
                supabase.table("user_karma").update({season_field: True}).eq("username", name).execute()

            # Check Seasonal & Rare
            row = supabase.table("user_karma").select("*").eq("username", name).execute().data[0]
            check_seasonal_and_rare(name, row)
    except Exception as e:
        print(f"⚠️ Achievement ladder failed: {e}")


    return old_k2, new_k, flair, total_delta, ("; ".join(extras) if extras else "")

# =========================
# Routing: new items
# =========================
def handle_new_item(item):
    """Only process new, not-yet-moderated items; apply guardrails and route."""
    if item.author is None or item.id in seen_ids:
        return
    if already_moderated(item):
        print(f"⏩ Skipping {item.id} (already moderated)")
        seen_ids.add(item.id)
        return
    seen_ids.add(item.id)

    author_name = str(item.author)
    bot_username = os.getenv("REDDIT_USERNAME", "").lower()

    if author_name.lower() == bot_username:
        print(f"🤖 skipping queue for bot's own post/comment {item.id}")
        return

    res = supabase.table("user_karma").select("*").eq("username", author_name).execute()
    karma = int(res.data[0]["karma"]) if res.data else 0

    # Language hinting
    text = item_text(item)
    if not likely_english(text):
        print("🈺 Language hint → manual")
        asyncio.run_coroutine_threadsafe(
            send_discord_approval(item, lang_label="Maybe non-English", note="Language hint"),
            bot.loop
        )
        return

    # Night Guard
    now_local = datetime.now(current_tz())
    if in_night_guard_window(now_local) and karma < NIGHT_GUARD_MIN_KARMA:
        print(f"🌙 Night Guard: u/{author_name} ({karma} < {NIGHT_GUARD_MIN_KARMA}) → manual")
        asyncio.run_coroutine_threadsafe(
            send_discord_approval(item, lang_label="English", note="Night Guard window", night_guard_ping=True),
            bot.loop
        )
        return

    # AUTO-APPROVE path
        # AUTO-APPROVE path (either high karma OR bot itself)
    bot_username = os.getenv("REDDIT_USERNAME", "").lower()
    if karma >= 500 or author_name.lower() == bot_username:
        item.mod.approve()
        old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=False)

        # Option: prevent karma changes for the bot itself
        if author_name.lower() == bot_username:
            old_k, new_k, flair, total_delta, extras = 0, 0, "—", 0, ""

        note = f"+{total_delta}" + (f" ({extras})" if extras else "")
        print(f"✅ Auto-approved u/{author_name} ({old_k}→{new_k}) {note}")

        # also log to approval log channel
        asyncio.run_coroutine_threadsafe(
            log_approval(item, old_k, new_k, flair, note),
            bot.loop
        )
        return

    # Otherwise: manual review
    print(f"📨 Queueing u/{author_name} ({karma} karma) → manual")
    asyncio.run_coroutine_threadsafe(
        send_discord_approval(item, lang_label="English"),
        bot.loop
    )


# =========================
# Polling (PRAW)
# =========================
def reddit_polling():
    """Background polling for new subscribers + comments + posts."""
    print("🌍 Reddit polling started...")
    while True:
        try:
            
            # --- Existing logic: comments ---
            for comment in subreddit.comments(limit=10):
                handle_new_item(comment)

            # --- Existing logic: submissions ---
            for submission in subreddit.new(limit=5):
                handle_new_item(submission)

        except Exception as e:
            print(f"⚠️ Reddit poll error: {e}")
        time.sleep(15)

# =========================
# Karma decay loop (daily)
# =========================
def apply_decay_once():
    if not DECAY_ENABLED:
        return
    try:
        rows = supabase.table("user_karma").select("*").execute().data or []
    except Exception as e:
        print(f"⚠️ Decay query failed: {e}")
        return

    today_local = datetime.now(current_tz()).date()
    for row in rows:
        name = row.get("username")
        karma = int(row.get("karma", 0))
        if karma <= 0:
            continue

        last_approved = row.get("last_approved_date")
        last_decay = row.get("last_decay_date")
        try:
            la = date.fromisoformat(last_approved) if last_approved else None
        except Exception:
            la = None
        try:
            ld = date.fromisoformat(last_decay) if last_decay else None
        except Exception:
            ld = None

        since = (today_local - (la or today_local)).days
        if since == (DECAY_AFTER_DAYS - 1):
            flair = get_flair_for_karma(karma)
            asyncio.run_coroutine_threadsafe(
                send_decay_warning(name, since, karma, flair),
                bot.loop
            )
        
        if since <= DECAY_AFTER_DAYS:
            continue

        start_point = (la or today_local) + timedelta(days=DECAY_AFTER_DAYS)
        if ld:
            start_point = max(start_point, ld)

        days_to_decay = (today_local - start_point).days
        if days_to_decay <= 0:
            continue

        delta = -DECAY_PER_DAY * days_to_decay
        old_k, new_k, flair = apply_karma_and_flair(name, delta, allow_negative=False)
        try:
            supabase.table("user_karma").upsert({
                "username": name,
                "last_decay_date": today_local.isoformat(),
            }).execute()
        except Exception:
            pass
        print(f"🍂 Decay: u/{name} {old_k}→{new_k} (-{abs(delta)})")

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
                    ).eq("username", name).execute()

                # 1 Week Rule Opinion
                if days_active >= 7 and not row.get("feedback_1w_rule_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1w_rules"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1w_rule_sent": True}
                    ).eq("username", name).execute()

                # 1 Week Prompt Opinion
                if days_active >= 7 and not row.get("feedback_1w_prompt_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1w_prompts"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1w_prompt_sent": True}
                    ).eq("username", name).execute()

        except Exception as e:
            print(f"⚠️ Feedback loop error: {e}")

        time.sleep(86400)  # run once per day

# =========================
# Weekly Achievements Loop
# =========================
def get_weekly_achievements():
    """Fetch all badges unlocked in the past 7 days."""
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    res = supabase.table("user_badges").select("*").gte("unlocked_on", week_ago).execute()
    return res.data or []

def post_weekly_achievements():
    rows = get_weekly_achievements()
    if not rows:
        print("ℹ️ No achievements this week — skipping weekly post.")
        return
    
    text = format_weekly_achievements(rows)
    if not text:
        return

    title = "🌟 Weekly Naturist Achievements 🌿✨"
    try:
        # 👇 use OWNER account to post instead of Bot
        submission = reddit_owner.subreddit(SUBREDDIT_NAME).submit(title, selftext=text)
        submission.mod.approve()
        print("✅ Weekly achievements post auto-approved (by owner account)")
    except Exception as e:
        print(f"⚠️ Could not post weekly achievements: {e}")


def weekly_achievements_loop():
    print("🕒 Weekly achievements loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            # Run every Sunday at 12:00
            if now.weekday() == 6 and now.hour == 12 and now.minute == 0:
                post_weekly_achievements()
                time.sleep(60)  # avoid duplicate run in same minute
        except Exception as e:
            print(f"⚠️ Weekly achievements loop error: {e}")
        time.sleep(30)


def decay_loop():
    print("🕒 Decay loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            if now.hour == DECAY_RUN_HOUR:
                apply_decay_once()
                time.sleep(3600)
            else:
                time.sleep(300)
        except Exception as e:
            print(f"⚠️ Decay loop error: {e}")
            time.sleep(600)

# =========================
# SLA Monitor (re-post with PRIORITY + ETA refresh)
# =========================
async def _escalate_card(msg_id: int):
    entry = pending_reviews.get(msg_id)
    if not entry:
        return
    item = entry["item"]
    level = entry.get("level", 0) + 1

    # delete old message if still exists
    try:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        old_msg = await channel.fetch_message(msg_id)
        await old_msg.delete()
    except Exception:
        pass

    # re-post with higher priority marker (ETA recalculated inside)
    await send_discord_approval(
        item,
        lang_label="English",
        note=f"{SLA_PRIORITY_PREFIX}: waiting > {level * SLA_MINUTES} minutes",
        night_guard_ping=False,
        priority_level=level,
    )

def sla_loop():
    print("⏱️ SLA monitor started...")
    while True:
        try:
            now = time.time()
            for msg_id in list(pending_reviews.keys()):
                entry = pending_reviews.get(msg_id)
                if not entry:
                    continue
                last = entry.get("last_escalated_ts", entry.get("created_ts", now))
                if now - last >= SLA_MINUTES * 60:
                    entry["last_escalated_ts"] = now
                    asyncio.run_coroutine_threadsafe(_escalate_card(msg_id), bot.loop)
                    pending_reviews.pop(msg_id, None)
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ SLA loop error: {e}")
            time.sleep(30)

# =========================
# Daily Prompt Poster (Trivia / Mindfulness)
# =========================
def daily_prompt_poster():
    print("🕒 Daily prompt loop started...")
    while True:
        try:
            now = datetime.now(current_tz())

            # Runs once per day at 12:00
            if now.hour == 12 and now.minute == 0:
                today = now.date().isoformat()

                # Check if already posted today
                res = supabase.table("daily_bodypositive").select("*").eq("date_posted", today).execute()
                if res.data:
                    print("ℹ️ Body positivity already posted today, skipping.")
                    time.sleep(60)
                    continue

                # Always body positivity
                prompt = generate_body_positive()
                title = "💚 Body Positivity Prompt"

                # Submit post
                submission = subreddit.submit(title, selftext=prompt)

                # ✅ Auto-approve bot’s own daily posts
                try:
                    submission.mod.approve()
                    print("✅ Auto-approved Daily Prompt post")
                except Exception as e:
                    print(f"⚠️ Could not auto-approve Daily Prompt post: {e}")
                # Log bot's own post to Discord
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
                time.sleep(60)  # avoid double posting in same minute

        except Exception as e:
            print(f"⚠️ Daily prompt error: {e}")

        time.sleep(30)
        
def daily_fact_poster():
    print("🕒 Daily fact loop started...")
    while True:
        try:
            now = datetime.now(current_tz())

            # Runs once per day at 08:00 (midnight)
            if now.hour == 8 and now.minute == 0:
                today = now.date().isoformat()

                # Skip if already posted today
                res = supabase.table("daily_facts").select("*").eq("date_posted", today).execute()
                if res.data:
                    print("ℹ️ Fact already posted today, skipping.")
                    time.sleep(60)
                    continue

                fact = generate_naturist_fact()
                title = "🌿 Naturist Fact of the Day"

                # Submit post
                submission = subreddit.submit(title, selftext=fact)

                # ✅ Auto-approve bot’s own daily posts
                try:
                    submission.mod.approve()
                    print("✅ Auto-approved Naturist Fact post")
                except Exception as e:
                    print(f"⚠️ Could not auto-approve Naturist Fact post: {e}")
                
                # Log bot's own post to Discord
                asyncio.run_coroutine_threadsafe(
                    send_discord_auto_log(
                        submission,
                        old_k=0, new_k=0,
                        flair="Daily Prompt",
                        awarded_points=0,
                        extras_note="Bot daily fact post"
                    ),
                    bot.loop
                )
                
                # Apply Daily Prompt flair (reuse same one if you want)
                daily_flair_id = flair_templates.get("Daily Prompt")
                if daily_flair_id:
                    try:
                        submission.flair.select(daily_flair_id)
                        print("🏷️ Flair set to Daily Prompt")
                    except Exception as e:
                        print(f"⚠️ Could not set flair: {e}")

                print(f"📢 Posted daily fact: {title}")
                time.sleep(60)

        except Exception as e:
            print(f"⚠️ Daily fact error: {e}")

        time.sleep(30)
# =========================
# Discord events
# =========================
@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    # Restore reviews from Supabase
    restore_pending_reviews()
    threading.Thread(target=reddit_polling, daemon=True).start()
    threading.Thread(target=reddit_dm_polling, daemon=True).start()
    threading.Thread(target=decay_loop, daemon=True).start()
    threading.Thread(target=sla_loop, daemon=True).start()
    threading.Thread(target=daily_prompt_poster, daemon=True).start()
    threading.Thread(target=daily_fact_poster, daemon=True).start()
    threading.Thread(target=feedback_loop, daemon=True).start()
    threading.Thread(target=weekly_achievements_loop, daemon=True).start()

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    print(f"➡️ Reaction received: {reaction.emoji} by {user} on msg {msg_id}")

    # Check if the message is still tracked
    if msg_id not in pending_reviews:
        print("⚠️ Reaction ignored — no pending review entry for this message.")
        await reaction.message.channel.send("⚠️ This review card is no longer active.")
        return

    entry = pending_reviews.pop(msg_id, None)
    delete_pending_review(msg_id)
    if not entry:
        print("⚠️ Entry missing even though msg_id was in pending_reviews.")
        return

    item = entry["item"]
    author_name = str(item.author)

    try:
        # ✅ APPROVE
        if str(reaction.emoji) == "✅":
            print(f"✅ Approving u/{author_name}...")
            item.mod.approve()
            old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=True)
            note = f"+{total_delta}" + (f" ({extras})" if extras else "")

            await reaction.message.channel.send(
                f"✅ Approved u/{author_name} ({old_k} → {new_k}) {note}, flair: {flair}"
            )
            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)
            await log_approval(item, old_k, new_k, flair, note, extras)
            print(f"✅ Approval done for u/{author_name}")

        # ❌ REJECT
        elif str(reaction.emoji) == "❌":
            print(f"❌ Rejecting u/{author_name}...")
            item.mod.remove()
            old_k, new_k, flair = apply_karma_and_flair(item.author, -1, allow_negative=True)

            await reaction.message.channel.send(
                f"❌ Removed u/{author_name}'s item ({old_k} → {new_k}), flair: {flair}."
            )

            # Add rule reactions to pick rejection reason
            review_msg = reaction.message
            for emoji in REJECTION_REASONS.keys():
                await review_msg.add_reaction(emoji)

            def check(r, u):
                return (
                    r.message.id == review_msg.id
                    and u.id == user.id
                    and str(r.emoji) in REJECTION_REASONS
                )

            try:
                reason_reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reason_reaction.emoji) == "✏️":
                    prompt_msg = await reaction.message.channel.send(
                        f"{user.mention}, please type the custom rejection reason (60s timeout):"
                    )
                    msg = await bot.wait_for(
                        "message",
                        timeout=60.0,
                        check=lambda m: m.author == user and m.channel == reaction.message.channel
                    )
                    reason_text = f"Custom: {msg.content}"
                    try:
                        await prompt_msg.delete()
                        await msg.delete()
                    except Exception as e:
                        print(f"⚠️ Could not delete custom reason messages: {e}")
                else:
                    reason_text = REJECTION_REASONS[str(reason_reaction.emoji)]

                # DM Reddit user
                try:
                    redditor = reddit.redditor(author_name)
                    redditor.message(
                        f"❌ Your post/comment was removed from r/{SUBREDDIT_NAME}",
                        f"Reason: {reason_text}\n\nPlease review the subreddit rules before posting again."
                    )
                    print(f"📩 Sent rejection DM to u/{author_name}")
                except Exception as e:
                    print(f"⚠️ Could not DM u/{author_name}: {e}")

                # Log rejection
                await log_rejection(item, old_k, new_k, flair, reason_text)
                print(f"❌ Rejection logged for u/{author_name}")

            except asyncio.TimeoutError:
                await reaction.message.channel.send("⏳ No rejection reason chosen, skipping DM/log reason.")
                print("⚠️ Timeout waiting for rejection reason.")

            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)

        else:
            print(f"ℹ️ Ignored reaction {reaction.emoji} (not ✅ or ❌).")

    except Exception as e:
        print(f"🔥 Error handling reaction {reaction.emoji} for u/{author_name}: {e}")



# =========================
# Start
# =========================
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
