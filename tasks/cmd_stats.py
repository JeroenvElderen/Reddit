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
