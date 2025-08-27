def on_first_approval_welcome(item, author_name: str, old_karma: int):
    if not WELCOME_ENABLED or old_karma != 0:
        return
    try:
        text = (
            f"Hey u/{author_name} — welcome to r/{SUBREDDIT_NAME}! 🌞\n\n"
            "Thanks for contributing. Please remember:\n"
            "• Be respectful & follow our community rules\n"
            "• Blur faces / remove location data if needed\n"
            "• Use clear titles and context for photos\n"
            "• Try `!help` in a DM to me for commands\n\n"
            "Happy posting! 🌿"
        )
        item.reply(text)
        print(f"👋 Welcome reply posted for u/{author_name}")
    except Exception as e:
        print(f"⚠️ Welcome reply failed: {e}")
