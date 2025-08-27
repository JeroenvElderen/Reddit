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
