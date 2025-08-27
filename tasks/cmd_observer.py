def cmd_observer(author: str, message):
    """Let users self-assign the Quiet Observer flair (karma reset to 0)."""
    flair_id = flair_templates.get("Quiet Observer")
    if flair_id:
        try:
            subreddit.flair.set(redditor=author, flair_template_id=flair_id)
            supabase.table("user_karma").upsert({
                "username": author,
                "karma": 0,   # 👈 reset karma
                "last_flair": "Quiet Observer"
            }).execute()
            message.reply(
                "🌙 You are now a **Quiet Observer 🌿**.\n\n"
                "Your karma has been reset to 0. "
                "You can still earn karma and climb back into the flair ladder anytime you contribute 🌞"
            )
            print(f"🌙 u/{author} set themselves to Quiet Observer (karma reset to 0)")
        except Exception as e:
            message.reply("⚠️ Sorry, I couldn’t set your Observer flair right now.")
            print(f"⚠️ Failed to set Quiet Observer flair for {author}: {e}")
