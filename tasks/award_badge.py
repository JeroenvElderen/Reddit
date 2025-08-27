def award_badge(username: str, badge_name: str):
    """Generic badge award helper (Observer ladder), now with duplicate guard + logging."""
    if _badge_exists(username, badge_name):
        return

    try:
        supabase.table("user_badges").upsert({
            "username": username,
            "badge": badge_name,
            "unlocked_on": datetime.utcnow().isoformat()
        }).execute()
        print(f"🌙 Observer badge unlocked: {badge_name} for u/{username}")

        # ✅ Log to Discord
        asyncio.run_coroutine_threadsafe(log_achievement(username, badge_name), bot.loop)

        # Optional: DM user from owner account
        try:
            reddit_owner.redditor(username).message(
                "🌙 New Observer Achievement!",
                f"Congrats u/{username}! You just earned **{badge_name}** 🏆\n\n"
                f"Your time as an Observer is part of your naturist journey 🌿"
            )
        except Exception as e:
            print(f"⚠️ Could not DM Observer badge to {username}: {e}")

    except Exception as e:
        print(f"⚠️ Could not save Observer badge for {username}: {e}")
