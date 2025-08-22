import os
import time
import json
import threading
import asyncio
from datetime import datetime, date, timedelta, timezone, time as dtime
from urllib.parse import urlparse

import praw
import discord
from discord.ext import commands
from supabase import create_client, Client

# =========================
# Supabase
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# Reddit (PRAW, sync)
# =========================
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)
SUBREDDIT_NAME = "PlanetNaturists"
subreddit = reddit.subreddit(SUBREDDIT_NAME)

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
}

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
    name = str(user_or_name)
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
# Decay Warning Helpers
# =========================
async def send_decay_warning(username: str, days_since: int, karma: int, flair: str):
    """DM the user and log to a separate Discord channel when they are close to decay."""
    try:
        redditor = reddit.redditor(username)
        msg = (
            f"Hey u/{username}, just a friendly reminder 🌞\n\n"
            f"You haven’t had an approved post or comment in **{days_since} days**. "
            f"After {DECAY_AFTER_DAYS} days, your community karma will start to decay and you may lose your flair.\n\n"
            "Stay active to keep your streak alive and your flair growing! 🌿"
        )
        redditor.message(f"⚠️ Reminder: Stay active in r/{SUBREDDIT_NAME}", msg)
        print(f"📩 Sent decay warning to u/{username}")

        # Log to Discord (separate channel)
        channel = bot.get_channel(DISCORD_DECAY_LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="⚠️ Decay Warning Sent",
                description=f"u/{username} warned (inactive {days_since}d, decay in {DECAY_AFTER_DAYS - days_since}d)",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Current Karma", value=str(karma), inline=True)
            embed.add_field(name="Flair", value=flair, inline=True)
            await channel.send(embed=embed)
    except Exception as e:
        print(f"⚠️ Failed to send DM/log warning for {username}: {e}")

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

    title_prefix = f"{SLA_PRIORITY_PREFIX} (L{priority_level}) · " if priority_level > 0 else ""
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


async def log_rejection(item, old_k: int, new_k: int, flair: str):
    """Log full rejection info to the rejection log channel."""
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
            "• Use clear titles and context for photos\n\n"
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
    if karma >= 500:   # ✅ now inside the function
        item.mod.approve()
        old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=False)
        note = f"+{total_delta}" + (f" ({extras})" if extras else "")
        print(f"✅ Auto-approved u/{author_name} ({old_k}→{new_k}) {note}")

        # send the auto-approval log to review channel (for context)
        asyncio.run_coroutine_threadsafe(
            send_discord_auto_log(item, old_k, new_k, flair, total_delta, extras_note=extras),
            bot.loop
        )

        # also log to approval log channel
        asyncio.run_coroutine_threadsafe(
            log_approval(author_name, old_k, new_k, flair, note),
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
    """Background polling for new comments + posts."""
    print("🌍 Reddit polling started...")
    while True:
        try:
            for comment in subreddit.comments(limit=10):
                handle_new_item(comment)
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
# Discord events
# =========================
@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    threading.Thread(target=reddit_polling, daemon=True).start()
    threading.Thread(target=decay_loop, daemon=True).start()
    threading.Thread(target=sla_loop, daemon=True).start()

@bot.event
async def on_reaction_add(reaction, user):
    """Manual review: ✅ approve (award), ❌ reject (−1). 
    Decision lock applied + ETA metrics. 
    Also logs approvals/rejections to separate channels.
    """
    if user.bot:
        return
    msg_id = reaction.message.id
    if msg_id not in pending_reviews:
        return

    entry = pending_reviews.pop(msg_id, None)
    if not entry:
        return

    item = entry["item"]
    author_name = str(item.author)

    # ✅ APPROVE
    if str(reaction.emoji) == "✅":
        item.mod.approve()
        old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=True)
        note = f"+{total_delta}" + (f" ({extras})" if extras else "")

        # confirmation in review channel
        await reaction.message.channel.send(
            f"✅ Approved u/{author_name} ({old_k} → {new_k}) {note}, flair: {flair}"
        )

        # record ETA metric
        record_mod_decision(entry.get("created_ts"), user.id)

        # lock and delete review card
        await _lock_and_delete_message(reaction.message)

        # log to approval log channel
        await log_approval(item, old_k, new_k, flair, note, extras)

    # ❌ REJECT
    elif str(reaction.emoji) == "❌":
        item.mod.remove()
        old_k, new_k, flair = apply_karma_and_flair(item.author, -1, allow_negative=True)

        # confirmation in review channel
        await reaction.message.channel.send(
            f"❌ Removed u/{author_name}'s item ({old_k} → {new_k}), flair: {flair}"
        )

        # record ETA metric
        record_mod_decision(entry.get("created_ts"), user.id)

        # lock and delete review card
        await _lock_and_delete_message(reaction.message)

        # log to rejection log channel
        await log_rejection(item, old_k, new_k, flair)


# =========================
# Start
# =========================
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
