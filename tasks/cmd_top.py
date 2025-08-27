def cmd_top(author: str, message):
    posts = list(subreddit.top(time_filter="week", limit=5))
    lines = [
        f"{i+1}. [{p.title}](https://reddit.com{p.permalink}) — {p.score} upvotes"
        for i, p in enumerate(posts)
    ]
    message.reply("🌞 **Top Posts This Week** 🌿\n\n" + "\n".join(lines))
