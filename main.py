"""
Entry point for RedditBot.
"""

import os
from app.clients.discord_bot import bot  
import app.events.discord_handlers      

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌ DISCORD_TOKEN is missing from environment.")
    print("🚀 Starting Discord bot...")
    bot.run(token)


if __name__ == "__main__":
    main()
