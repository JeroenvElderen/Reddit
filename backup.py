"""
Entry point for RedditBot.
"""

import os
from app.clients.discord_bot import bot  # loads the discord client + intents
import app.events.discord_handlers       # registers on_ready, on_reaction_add

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌ DISCORD_TOKEN is missing from environment.")
    print("🚀 Starting Discord bot...")
    bot.run(token)


if __name__ == "__main__":
    main()
