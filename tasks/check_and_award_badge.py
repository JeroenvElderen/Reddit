def check_and_award_badge(username: str, field: str, count: int):
    """Check if a user unlocked a new badge level, replacing old levels and logging to Discord."""
    level = sum(1 for t in BADGE_THRESHOLDS if count >= t)
    if level == 0:
        return

    base = field.replace("_posts_count", "").replace("_", " ").title()
    badge_name = f"{base} {badge_level_label(level, len(BADGE_THRESHOLDS))}"

    # 🚫 avoid duplicate re-log
    if _badge_exists(username, badge_name):
        return

    try:
        supabase.table("user_badges").delete().eq("username", username).ilike("badge", f"{base} %").execute()
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": badge_name,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌟 Badge updated: {badge_name} for u/{username}")

        # log
        asyncio.run_coroutine_threadsafe(log_achievement(username, badge_name), bot.loop)

        # optional DM
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
