"""
Entry point for RedditBot.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app.clients.discord_bot import bot
import app.events.discord_handlers
import app.events.legal_map
import app.commands.discord_cah
import app.commands.discord_achievements
import app.cah.cards_add 
import app.cah.cards_remove 
import app.cah.cards_list 
import app.cah.packs_list 
import app.cah.packs_toggle

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌ DISCORD_TOKEN is missing from environment.")
    print("🚀 Starting Discord bot...")
    bot.run(token)


if __name__ == "__main__":
    main()
