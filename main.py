import os
import asyncio
import discord
from discord.ext import commands, tasks
import asyncpraw
from datetime import datetime, timezone

# ====== CONFIG ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "PlanetNaturistsBot"

SUBREDDITS = ["all"]  # change to your target subreddit(s)
SCAN_INTERVAL = 60  # seconds
DAILY_RESCAN_HOUR = 12  # 12:00 UTC

# ====== DISCORD SETUP ======
intents = discord.Intents.default()
intents.message_content = True  # required for reading content
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== REDDIT SETUP ======
reddit = asyncpraw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Track seen IDs to avoid reprocessing old posts/comments
seen_ids = set()


# ====== HELPERS ======
async def send_to_discord(item, item_type="comment"):
    """Send Reddit post/comment to Discord for approval"""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("⚠️ Discord channel not found!")
        return

    if item_type == "comment":
        content = f"💬 **New Comment by u/{item.author}**\n{item.body[:500]}...\n🔗 https://reddit.com{item.permalink}"
    else:
        content = f"📜 **New Post by u/{item.author}**\n**{item.title}**\n{item.selftext[:500]}...\n🔗 https://reddit.com{item.permalink}"

    msg = await channel.send(content)

    # Add approval / rejection reactions
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")


async def process_item(item, item_type):
    """Check if item is new and handle it"""
    if item.id in seen_ids:
        return  # skip old/duplicate items
    seen_ids.add(item.id)

    await send_to_discord(item, item_type=item_type)


# ====== POLLING TASKS ======
async def poll_comments():
    """Poll subreddit comments"""
    await bot.wait_until_ready()
    print("💬 Comment polling started...")

    try:
        subreddit = await reddit.subreddit("+".join(SUBREDDITS))
        while not bot.is_closed():
            try:
                async for comment in subreddit.stream.comments(skip_existing=True):
                    await process_item(comment, "comment")
            except Exception as e:
                print(f"⚠️ Comment poll error: {e}")
                await asyncio.sleep(SCAN_INTERVAL)
    except Exception as e:
        print(f"❌ Fatal comment poll error: {e}")


async def poll_posts():
    """Poll subreddit submissions"""
    await bot.wait_until_ready()
    print("📜 Post polling started...")

    try:
        subreddit = await reddit.subreddit("+".join(SUBREDDITS))
        while not bot.is_closed():
            try:
                async for post in subreddit.stream.submissions(skip_existing=True):
                    await process_item(post, "post")
            except Exception as e:
                print(f"⚠️ Post poll error: {e}")
                await asyncio.sleep(SCAN_INTERVAL)
    except Exception as e:
        print(f"❌ Fatal post poll error: {e}")


# ====== DAILY RESCAN ======
@tasks.loop(minutes=60)
async def daily_rescan():
    """Run a daily rescan for missed posts/comments"""
    now = datetime.now(timezone.utc)
    if now.hour == DAILY_RESCAN_HOUR:
        print("⏰ Daily rescan...")
        try:
            subreddit = await reddit.subreddit("+".join(SUBREDDITS))

            async for post in subreddit.new(limit=10):
                await process_item(post, "post")

            async for comment in subreddit.comments(limit=10):
                await process_item(comment, "comment")

        except Exception as e:
            print(f"⚠️ Daily rescan error: {e}")


# ====== EVENTS ======
@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    bot.loop.create_task(poll_comments())
    bot.loop.create_task(poll_posts())
    daily_rescan.start()


# ====== REACTIONS ======
@bot.event
async def on_raw_reaction_add(payload):
    """Handle approval (✅) or rejection (❌)"""
    if payload.user_id == bot.user.id:
        return  # ignore bot's own reactions

    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if str(payload.emoji) == "✅":
        await message.reply("✅ Approved!")
    elif str(payload.emoji) == "❌":
        await message.reply("❌ Rejected!")


# ====== START ======
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)