def cmd_rules(author: str, message):
    rules_text = "\n".join([f"{emoji} {text}" for emoji, text in REJECTION_REASONS.items()])
    message.reply(f"📜 **r/{SUBREDDIT_NAME} Rules**\n\n{rules_text}")
