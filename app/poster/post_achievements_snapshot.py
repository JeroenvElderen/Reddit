"""
Post lifetime achievements snapshot to Reddit.
"""

from datetime import datetime, timedelta
from app.clients.supabase import supabase
from app.clients.reddit_owner import reddit_owner
from app.models.state import SUBREDDIT_NAME
from app.models.badges_meta import META_TITLES


def get_weekly_achievements():
    """Fetch all badges unlocked in the past 7 days."""
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    res = supabase.table("user_badges").select("*").gte("unlocked_on", week_ago).execute()
    return res.data or []


def post_weekly_achievements():
    """Post a lifetime snapshot of everyone's latest badges (only highest level per ladder)."""
    try:
        all_rows = supabase.table("user_badges").select("*").execute().data or []
    except Exception as e:
        print(f"⚠️ Could not fetch badges: {e}")
        return

    if not all_rows:
        text = (
            "🌟🌿🌞🌿🌟\n"
            "✨ Naturist Achievements Snapshot ✨\n"
            "🌟🌿🌞🌿🌟\n\n"
            "No achievements yet — be the first to unlock one! 🌱"
        )
        title = "🌟 Naturist Achievements Snapshot 🌿✨"
        try:
            submission = reddit_owner.subreddit(SUBREDDIT_NAME).submit(title, selftext=text)
            submission.mod.approve()
            print("✅ Empty achievements snapshot posted")
        except Exception as e:
            print(f"⚠️ Could not post empty achievements snapshot: {e}")
        return

    # --- Categorization helpers ---
    meta_titles = set(META_TITLES)
    observer_keys = [
        "Still Waters", "Deep Reflection", "Silent Strength",
        "Quiet Voice", "Gentle Helper", "Guiding Light",
        "First Step", "Comeback Trail", "Resilient Spirit",
        "Friendly Observer", "Encourager", "Community Whisper"
    ]
    seasonal_rare = ["Seasonal Naturist", "Festival Free Spirit", "Naturist Traveler"]

    location_keywords = [
        "Beach","Forest","Lake","Mountain","Meadow","River",
        "Pool","Backyard","Camping","Sauna","Resort","Island",
        "Countryside","Cave","Tropical","Nordic","Festival"
    ]

    def is_meta(b: str) -> bool:
        return any(t in b for t in meta_titles)

    def is_observer(b: str) -> bool:
        return any(k in b for k in observer_keys)

    def is_seasonal_or_rare(b: str) -> bool:
        return any(k in b for k in seasonal_rare)

    def is_location(b: str) -> bool:
        return any(k in b for k in location_keywords)

    # --- Bucketize by user ---
    users = {}
    for row in all_rows:
        u = row["username"]
        b = row["badge"]
        users.setdefault(u, {"meta": [], "locations": [], "pillars": [], "observer": [], "special": []})
        if is_meta(b):
            users[u]["meta"].append(b)
        elif is_observer(b):
            users[u]["observer"].append(b)
        elif is_seasonal_or_rare(b):
            users[u]["special"].append(b)
        elif is_location(b):
            users[u]["locations"].append(b)
        else:
            users[u]["pillars"].append(b)

    # --- Build the post body ---
    parts = []
    parts.append("🌟🌿🌞🌿🌟\n✨ Naturist Achievements — Lifetime Snapshot ✨\n🌟🌿🌞🌿🌟\n")

    # Meta
    meta_lines = [f"• u/{u} → {', '.join(sorted(bags['meta']))}" for u, bags in users.items() if bags["meta"]]
    if meta_lines:
        parts.append("👑 **Meta Ladder**")
        parts.extend(meta_lines)
        parts.append("\n🌿🌿🌿🌿🌿\n")

    # Locations
    loc_lines = [f"• u/{u} → {', '.join(sorted(bags['locations']))}" for u, bags in users.items() if bags["locations"]]
    if loc_lines:
        parts.append("🏖️ **Location Achievements**")
        parts.extend(loc_lines)
        parts.append("\n🌿🌿🌿🌿🌿\n")

    # Pillars
    pillar_lines = [f"• u/{u} → {', '.join(sorted(bags['pillars']))}" for u, bags in users.items() if bags["pillars"]]
    if pillar_lines:
        parts.append("🧘 **Pillar Progress**")
        parts.extend(pillar_lines)
        parts.append("\n🌿🌿🌿🌿🌿\n")

    # Observer
    obs_lines = [f"• u/{u} → {', '.join(sorted(bags['observer']))}" for u, bags in users.items() if bags["observer"]]
    if obs_lines:
        parts.append("🌙 **Quiet Observer Achievements**")
        parts.extend(obs_lines)
        parts.append("\n🌿🌿🌿🌿🌿\n")

    # Special
    special_lines = [f"• u/{u} → {', '.join(sorted(bags['special']))}" for u, bags in users.items() if bags["special"]]
    if special_lines:
        parts.append("🎉 **Special Unlocks**")
        parts.extend(special_lines)
        parts.append("\n🌿🌿🌿🌿🌿\n")

    parts.append("🌞💚 Keep shining, sharing, and celebrating naturism! ✨🌿")
    text = "\n".join(parts)

    title = "🌟 Naturist Achievements — Lifetime Snapshot 🌿✨"
    try:
        submission = reddit_owner.subreddit(SUBREDDIT_NAME).submit(title, selftext=text)
        submission.mod.approve()
        print("✅ Lifetime achievements snapshot posted")
    except Exception as e:
        print(f"⚠️ Could not post lifetime achievements snapshot: {e}")
