"""
Loop for polling Reddit DMs and dispatching commands.
"""

import praw
from app.clients.reddit_bot import reddit
from app.commands.reddit_dm import COMMANDS


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
                    try:
                        handler(author, message)
                        print(f"✅ Executed {command} for u/{author}")
                    except Exception as handler_error:
                        print(
                            f"🔥 Error executing {command} for u/{author}: {handler_error}"
                        )
                        try:
                            message.reply(
                                "⚠️ Sorry, I ran into an issue handling that command. "
                                "Please try again in a few minutes."
                            )
                        except Exception as reply_error:
                            print(
                                f"⚠️ Failed to reply about error for {command} from u/{author}: {reply_error}"
                            )
                else:
                    message.reply(
                        f"⚠️ Unknown command `{command}`.\n"
                        f"Type `!help` to see available commands."
                    )
                    print(f"⚠️ Unknown command {command} from u/{author}")

        except Exception as e:
            print(f"⚠️ Error processing DM: {e}")
