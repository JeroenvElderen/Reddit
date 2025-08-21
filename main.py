import praw
import os
import time
import threading
from supabase import create_client, Client
import discord
from discord.ext import commands

# ---- Supabase Setup ----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Reddit Setup ----
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

SUBREDDIT_NAME = "PlanetNaturists"
subreddit = reddit.subreddit(SUBREDDIT_NAME)

# ---- Flair Ladder ----
flair_ladder = [
    ("Cover Curious", 0),
    ("First Bare", 10),
    ("Skin Fresh", 50),
    ("Sun Chaser", 100),
    ("Breeze Walker", 250),
    ("Clothing Free", 500),
    ("Open Air", 1000),
    ("True Naturist", 2000),
    ("Bare Master", 5000),
    ("Naturist Legend", 10000)
]

# ---- Flair Templates ----
flair_templates = {
    "Cover Curious": "ae791af4-7d22-11f0-934a-2e3446070201",
    "First Bare": "bbf4d5d8-7d22-11f0-b485-d64b23d9d74f",
    "Skin Fresh": "c5be4a5e-7d22-11f0-b278-0298fe10eba2",
    "Sun Chaser": "d72ca790-7d22-11f0-a0de-a687510f7c1a",
    "Breeze Walker": "e35fc826-7d22-11f0-8742-d64b23d9d74f",
    "Clothing Free": "f01b2e02-7d22-11f0-bee0-7e43d54e1cf4",
    "Open Air": "7cfdbc2c-7dd7-11f0-9936-9e1c00b89022",
    "True Naturist": "8a5fbeb0-7dd7-11f0-9fa7-2e98a4cf4302",
    "Bare Master": "987da246-7dd7-11f0-ae7f-8206f7eb2e0a",
    "Naturist Legend": "a3f1f8fc-7dd7-11f0-b2c1-227301a06778"
}

# ---- Discord Setup ----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Store pending approvals (message_id -> reddit item)
pending_reviews = {}


def get_flair_for_karma(username: str, karma: int) -> str:
    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked


def update_user_karma(user, points=1):
    if user is None:
        return

    name = str(user)
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    current_karma = res.data[0]["karma"] if res.data else 0

    new_karma = max(0, current_karma + points)
    new_flair = get_flair_for_karma(name, new_karma)

    supabase.table("user_karma").upsert({
        "username": name,
        "karma": new_karma,
        "last_flair": new_flair
    }).execute()

    flair_id = flair_templates.get(new_flair)
    if flair_id:
        subreddit.flair.set(redditor=user, flair_template_id=flair_id)
        print(f"✅ Flair set for {name} → {new_flair} ({new_karma} karma)")


async def send_to_discord(item):
    """Send new Reddit item to Discord with approval buttons"""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    if hasattr(item, "title"):
        title = item.title
        content = (item.selftext[:200] + "...") if item.selftext else ""
        kind = "Post"
    else:
        title = "Comment"
        content = item.body[:200] + "..."
        kind = "Comment"

    embed = discord.Embed(
        title=f"New {kind} from u/{item.author}",
        description=content,
        url=f"https://reddit.com{item.permalink}",
        color=0x3498db
    )
    embed.set_footer(text=f"Karma will be updated on approval")

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    # Store for later approval
    pending_reviews[msg.id] = item
    print(f"⏳ Sent {kind} from {item.author} to Discord for approval.")


def handle_new_item(item):
    if item.author is None:
        return
    # Push to Discord
    coro = send_to_discord(item)
    bot.loop.create_task(coro)


def run_reddit_stream():
    print("🌍 Reddit stream started...")
    for comment in subreddit.stream.comments(skip_existing=True):
        handle_new_item(comment)
    for submission in subreddit.stream.submissions(skip_existing=True):
        handle_new_item(submission)


@bot.event
async def on_ready():
    print(f"✅ Discord bot logged in as {bot.user}")


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    if msg_id not in pending_reviews:
        return

    item = pending_reviews.pop(msg_id)

    if str(reaction.emoji) == "✅":
        item.mod.approve()
        update_user_karma(item.author, 1)
        await reaction.message.channel.send(f"👍 Approved {item.author}")
    elif str(reaction.emoji) == "❌":
        item.mod.remove()
        await reaction.message.channel.send(f"❌ Rejected {item.author}")


# ---- Run both Discord & Reddit ----
if __name__ == "__main__":
    t1 = threading.Thread(target=run_reddit_stream, daemon=True)
    t1.start()

    bot.run(DISCORD_TOKEN)
