def check_pillar_badge(username: str, field: str, count: int):
    """Check pillar ladders, keep only highest level, log once."""
    level = sum(1 for t in PILLAR_THRESHOLDS if count >= t)
    if level == 0:
        return

    base = field.replace("_posts_count", "").replace("_", " ").title()
    badge_name = f"{base} {badge_level_label(level, len(PILLAR_THRESHOLDS))}"

    if _badge_exists(username, badge_name):
        return

    try:
        supabase.table("user_badges").delete().eq("username", username).ilike("badge", f"{base} %").execute()
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": badge_name,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌟 Pillar badge updated: {badge_name} for u/{username}")

        asyncio.run_coroutine_threadsafe(log_achievement(username, badge_name), bot.loop)

        try:
            reddit_owner.redditor(username).message(
                "🌟 New Naturist Achievement!",
                f"Congrats u/{username}! You just reached **{badge_name}** 🏆\n\n"
                f"Keep growing your naturist journey 🌿"
            )
        except Exception as e:
            print(f"⚠️ Could not DM pillar badge to {username}: {e}")

    except Exception as e:
        print(f"⚠️ Could not save pillar badge for {username}: {e}")
