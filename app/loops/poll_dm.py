"""Loop for polling Reddit DMs and dispatching commands."""

from __future__ import annotations

import time
import praw

from app.clients.reddit_bot import reddit
from app.commands.reddit_dm import COMMANDS
from app.persistence.dm_seen import has_processed, record_processed


def _handle_dm(message: praw.models.Message) -> None:
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
                        "⚠️ Failed to reply about error for"
                        f" {command} from u/{author}: {reply_error}"
                    )
        else:
            message.reply(
                f"⚠️ Unknown command `{command}`.\n"
                f"Type `!help` to see available commands."
            )
            print(f"⚠️ Unknown command {command} from u/{author}")


def reddit_dm_polling():
    print("📩 Reddit DM polling started...")

    while True:
        try:
            for message in reddit.inbox.stream(skip_existing=False):
                if message is None or not isinstance(message, praw.models.Message):
                    continue

                message_id = getattr(message, "id", None)
                if has_processed(message_id):
                    continue

                try:
                    _handle_dm(message)
                finally:
                    record_processed(message_id)
                    try:
                        message.mark_read()
                    except Exception as mark_error:
                        print(f"⚠️ Failed to mark DM {message_id} as read: {mark_error}")

        except Exception as e:
            print(f"⚠️ Error processing DM stream: {e}")
            time.sleep(5)
