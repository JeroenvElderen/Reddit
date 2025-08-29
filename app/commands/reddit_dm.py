"""
Reddit DM command handlers.
"""

from datetime import date
import asyncio

from app.models.state import SUBREDDIT_NAME, subreddit
from app.models.flair_ladder import flair_ladder, flair_templates
from app.models.ruleset import REJECTION_REASONS
from app.moderation.counters_backfill import backfill_location_counts
from app.moderation.karma_stats import get_user_stats
from app.clients.supabase import supabase
from app.config import DECAY_AFTER_DAYS
from app.models.spot import SpotSubmission
from app.moderation.spots import send_spot_submission
from app.clients.discord_bot import bot


# =========================
def cmd_recount(author: str, message):
    """Recalculate location & pillar counters + meta; update badges; reply with a summary."""
    result = backfill_location_counts(author)
    if not result:
        message.reply("⚠️ Sorry, I couldn’t recount your posts right now.")
        return

    loc_counts = result["locations"]
    pillar_counts = result["pillars"]
    total = result["total"]

    def fmt_counts(d: dict) -> str:
        lines = [
            f"- {k.replace('_posts_count','').replace('_',' ').title()}: {v}"
            for k, v in d.items() if v > 0
        ]
        return "\n".join(lines) if lines else "None"

    reply = (
        f"🔄 **Recount complete** for u/{author}\n\n"
        f"**Locations:**\n{fmt_counts(loc_counts)}\n\n"
        f"**Pillars:**\n{fmt_counts(pillar_counts)}\n\n"
        f"**Naturist total posts:** {total}\n\n"
        "I also checked & updated your achievements. 🎉"
    )
    message.reply(reply)


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

def cmd_spot(author: str, message):
    """Handle `!spot` submissions from Reddit users."""
    try:
        _, payload = message.body.split(" ", 1)
        parts = [p.strip() for p in payload.split("|")]
        if len(parts) < 2:
            raise ValueError

        name, description = parts[0], parts[1]

        from app.clients.mapbox import geocode

        coords = geocode(name)
        if not coords:
            raise ValueError
        lat, lon = coords
        
        spot = SpotSubmission(
            name=name,
            latitude=float(lat),
            longitude=float(lon),
            description=description,
            submitted_by=author,
        )
    except Exception:
        message.reply(
            "⚠️ Usage: `!spot Name | description`")
        return

    try:
        asyncio.run_coroutine_threadsafe(send_spot_submission(spot), bot.loop)
        message.reply(
            "📍 Thanks! Your spot submission is pending moderator review."
        )
    except Exception:
        message.reply("⚠️ Sorry, I couldn’t submit your spot right now.")

def cmd_badges(author: str, message):
    """Fetch badge rows from Supabase and reply with thresholds."""
    try:
        res = (
            supabase.table("user_badges")
            .select("badge")
            .eq("username", author)
            .execute()
        )
        earned = [row["badge"] for row in (res.data or [])]
    except Exception:
        message.reply("⚠️ Sorry, I couldn’t fetch your badges right now.")
        return

    if not earned:
        message.reply(f"🌿 u/{author}, you haven’t earned any badges yet. Keep participating!")
        return

    catalog = {}
    for table in ["badges_meta", "badges_location", "badges_pillars", "badges_observer"]:
        try:
            rows = supabase.table(table).select("badge, threshold").execute().data or []
            catalog.update({r["badge"]: r.get("threshold") for r in rows})
        except Exception:
            continue

    lines = []
    for b in earned:
        thr = catalog.get(b)
        lines.append(f"- {b} — {thr}" if thr is not None else f"- {b}")

    message.reply("🏅 **Your Badges** 🌿\n\n" + "\n".join(lines))

def cmd_help(author: str, message):
    commands = {
        "!stats": "See your karma, flair, streak",
        "!flairlist": "View all flair levels",
        "!rules": "Read subreddit rules",
        "!decay": "Check if you’re close to decay",
        "!top": "See this week’s top posts",
        "!safety": "Naturist safety tips",
        "!spot": "Submit a nudist spot for the map",
        "!badges": "List your earned badges",
        "!observer": "Get Quiet Observer flair",
        "!help": "Show this menu",
        "!recount": "Recalculate your location post counts",
    }
    message.reply(
        "🤖 **Available Commands** 🌿\n\n"
        + "\n".join([f"- {c} → {desc}" for c, desc in commands.items()])
        + "\n\nType any command in DM (e.g., `!stats`)."
    )


# =========================
# Quiet Observer Flair Command
# =========================
def cmd_observer(author: str, message):
    """Let users self-assign the Quiet Observer flair (karma reset to 0)."""
    flair_id = flair_templates.get("Quiet Observer")
    if flair_id:
        try:
            subreddit.flair.set(redditor=author, flair_template_id=flair_id)
            supabase.table("user_karma").upsert({
                "username": author,
                "karma": 0,
                "last_flair": "Quiet Observer"
            }).execute()
            message.reply(
                "🌙 You are now a **Quiet Observer 🌿**.\n\n"
                "Your karma has been reset to 0. "
                "You can still earn karma and climb back into the flair ladder anytime you contribute 🌞"
            )
            print(f"🌙 u/{author} set themselves to Quiet Observer (karma reset to 0)")
        except Exception as e:
            message.reply("⚠️ Sorry, I couldn’t set your Observer flair right now.")
            print(f"⚠️ Failed to set Quiet Observer flair for {author}: {e}")


# =========================
# Command registry
# =========================
COMMANDS = {
    "!stats": cmd_stats,
    "!flairlist": cmd_flairlist,
    "!rules": cmd_rules,
    "!decay": cmd_decay,
    "!top": cmd_top,
    "!safety": cmd_safety,
    "!spot": cmd_spot,
    "!badges": cmd_badges,
    "!observer": cmd_observer,
    "!help": cmd_help,
    "!recount": cmd_recount,
}
