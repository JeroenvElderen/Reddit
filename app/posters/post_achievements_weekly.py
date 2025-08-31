"""
Weekly achievements digest formatter + loop.
"""

import time
from datetime import datetime, timedelta
from app.clients.supabase import supabase
from app.clients.reddit_bot import reddit
from app.models.state import SUBREDDIT_NAME
from app.utils.tz import current_tz


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

        line = f"• u/{u} → {badge}"

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
# Weekly achievements loop
# =========================
def weekly_achievements_loop():
    print("🕒 Weekly achievements loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            # Run every Sunday at 12:00
            if now.weekday() == 6 and now.hour == 12 and now.minute == 0:
                week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
                res = supabase.table("user_badges").select("*").gte("unlocked_on", week_ago).execute()
                rows = res.data or []

                body = format_weekly_achievements(rows)
                if body:
                    title = "🌟 Weekly Naturist Achievements ✨"
                    try:
                        submission = reddit.subreddit(SUBREDDIT_NAME).submit(title, selftext=body)
                        submission.mod.approve()
                        print("✅ Weekly achievements digest posted")
                    except Exception as e:
                        print(f"⚠️ Could not post weekly achievements: {e}")
                else:
                    print("ℹ️ No new weekly achievements to post")

                time.sleep(60)  # avoid duplicate posting
        except Exception as e:
            print(f"⚠️ Weekly achievements loop error: {e}")
        time.sleep(30)
