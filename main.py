"""
Entry point for RedditBot.
"""

import os
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

from app.clients.discord_bot import bot
from app.error_server import run_server
import app.events.discord_handlers
import app.events.legal_map
import app.commands.discord_achievements

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌ DISCORD_TOKEN is missing from environment.")
    print("🚀 Starting Discord bot...")
    Thread(target=run_server, daemon=True).start()
    bot.run(token)


if __name__ == "__main__":
    main()
