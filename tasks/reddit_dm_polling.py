def reddit_dm_polling():
    print("📩 Reddit DM polling started...")
    for message in reddit.inbox.stream(skip_existing=True):
        try:
            if not isinstance(message, praw.models.Message):
                continue
            body = message.body.strip().lower()
            author = str(message.author)

            if body.startswith("!"):
                command = body.split()[0]  # first word
                handler = COMMANDS.get(command)
                if handler:
                    handler(author, message)
                    print(f"✅ Executed {command} for u/{author}")
                else:
                    message.reply(
                        f"⚠️ Unknown command `{command}`.\n"
                        f"Type `!help` to see available commands."
                    )
                    print(f"⚠️ Unknown command {command} from u/{author}")

        except Exception as e:
            print(f"⚠️ Error processing DM: {e}")
