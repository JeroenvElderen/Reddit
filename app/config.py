import os
import json 
from pathlib import Path

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
DISCORD_DECAY_LOG_CHANNEL_ID = int(os.getenv("DISCORD_DECAY_LOG_CHANNEL_ID", "1408406356582731776"))
DISCORD_APPROVAL_LOG_CHANNEL_ID = int(os.getenv("DISCORD_APPROVAL_LOG_CHANNEL_ID", "1408406760322240572"))
DISCORD_REJECTION_LOG_CHANNEL_ID = int(os.getenv("DISCORD_REJECTION_LOG_CHANNEL_ID", "1408406824453148725"))
DISCORD_ACHIEVEMENTS_CHANNEL_ID = int(os.getenv("DISCORD_ACHIEVEMENTS_CHANNEL_ID", "1409902857947185202"))
DISCORD_UPVOTE_LOG_CHANNEL_ID = int(os.getenv("DISCORD_UPVOTE_LOG_CHANNEL_ID", "1409916507609235556"))
DISCORD_AUTO_APPROVAL_CHANNEL_ID = int(os.getenv("DISCORD_AUTO_APPROVAL_CHANNEL_ID", "1408406760322240572"))
DISCORD_FEEDBACK_LOG_CHANNEL_ID = int(os.getenv("DISCORD_FEEDBACK_LOG_CHANNEL_ID", "0"))

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")
LEGAL_MAP_CHANNEL_ID = int(os.getenv("LEGAL_MAP_CHANNEL_ID", "1411042968999166033"))
LEGAL_MAP_MARKERS_PATH = Path(__file__).resolve().parent.parent / "legal-map" / "markers.json"

# =========================
# CAH (Cards Against Humanity) game
# =========================
CAH_PAGE_SIZE = int(os.getenv("CAH_PAGE_SIZE", "20"))
CAH_ENABLED = os.getenv("CAH_ENABLED", "0") == "1"
CAH_POST_HOUR = int(os.getenv("CAH_POST_HOUR", "12"))
CAH_ROUND_DURATION_H = int(os.getenv("CAH_ROUND_DURATION_H", "24"))
CAH_EXTENSION_H = int(os.getenv("CAH_EXTENSION_H", "24"))
CAH_POST_FLAIR_ID = os.getenv("CAH_POST_FLAIR_ID") or None
DISCORD_CAH_CHANNEL_ID = int(os.getenv("DISCORD_CAH_CHANNEL_ID", "1410224656526610432"))

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

# ====== Queue ETA ======
ETA_SAMPLE_WINDOW_MIN = int(os.getenv("ETA_SAMPLE_WINDOW_MIN", "60"))
ETA_ACTIVE_REVIEWER_TIMEOUT_MIN = int(os.getenv("ETA_ACTIVE_REVIEWER_TIMEOUT_MIN", "10"))
ETA_MIN_SEC = int(os.getenv("ETA_MIN_SEC", "60"))          # floor 1 min
ETA_MAX_SEC = int(os.getenv("ETA_MAX_SEC", "3600"))        # ceiling 60 min
ETA_DEFAULT_DECISION_SEC = int(os.getenv("ETA_DEFAULT_DECISION_SEC", "180"))  # fallback avg 3 min

# Auto-tagger (post flair)
POST_FLAIR_IMAGE_ID = os.getenv("POST_FLAIR_IMAGE_ID", "")
POST_FLAIR_TEXT_ID = os.getenv("POST_FLAIR_TEXT_ID", "")
POST_FLAIR_LINK_ID = os.getenv("POST_FLAIR_LINK_ID", "")
POST_FLAIR_KEYWORDS = os.getenv("POST_FLAIR_KEYWORDS", "")

BOT_USERNAME = os.getenv("REDDIT_USERNAME", "").lower()
BOT_FLAIR_ID = os.getenv("BOT_FLAIR_ID", "")
OWNER_USERNAME = os.getenv("OWNER_REDDIT_USERNAME", "").lower()
SUBREDDIT_NAME = os.getenv("SUBREDDIT_NAME", "PlanetNaturists")

# ---------- Fixed flair mapping ---------- #
_fixed_flairs_path = Path(__file__).resolve().parent.parent / "fixed_flairs.json"
try:
    with _fixed_flairs_path.open() as f:
        FIXED_FLAIRS = {k.lower(): v for k, v in json.load(f).items()}
except FileNotFoundError:
    FIXED_FLAIRS = {}
if OWNER_USERNAME:
    FIXED_FLAIRS.setdefault(OWNER_USERNAME, "Naturist Legend")