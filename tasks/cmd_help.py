def cmd_help(author: str, message):
    commands = {
        "!stats": "See your karma, flair, streak",
        "!flairlist": "View all flair levels",
        "!rules": "Read subreddit rules",
        "!decay": "Check if you’re close to decay",
        "!top": "See this week’s top posts",
        "!safety": "Naturist safety tips",
        "!observer": "Get Quiet Observer flair",
        "!help": "Show this menu",
        "!recount": "Recalculate your location post counts",
    }
    message.reply(
        "🤖 **Available Commands** 🌿\n\n"
        + "\n".join([f"- {c} → {desc}" for c, desc in commands.items()])
        + "\n\nType any command in DM (e.g., `!stats`)."
    )
