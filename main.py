import os
import time
import threading
import praw
import discord
from discord.ext import commands
from supabase import create_client, Client

# ---- Supabase Setup ----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Reddit Setup (sync praw) ----
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

SUBREDDIT_NAME = "PlanetNaturists"
subreddit = reddit.subreddit(SUBREDDIT_NAME)

# ---- Discord Setup ----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

# ---- State ----
pending_reviews = {}  # discord_msg_id -> reddit item
seen_ids = set()      # already processed IDs


def get_flair_for_karma(karma: int) -> str:
    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked


def update_user_karma(user, points=1):
    """Increment karma & update flair in Supabase + Reddit."""
    if user is None:
        return

    name = str(user)
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    current_karma = res.data[0]["karma"] if res.data else 0

    new_karma = max(0, current_karma + points)
    new_flair = get_flair_for_karma(new_karma)

    supabase.table("user_karma").upsert({
        "username": name,
        "karma": new_karma,
        "last_flair": new_flair
    }).execute()

    flair_id = flair_templates.get(new_flair)
    if flair_id:
        subreddit.flair.set(redditor=user, flair_template_id=flair_id)
        print(f"✅ Flair set for {name} → {new_flair} ({new_karma} karma)")


async def send_discord_approval(item):
    """Send new Reddit item to Discord for approval."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("⚠️ Discord channel not found")
        return

    if hasattr(item, "title"):  # post
        preview = (item.selftext[:200] + "...") if item.selftext else ""
        item_type = "Post"
    else:  # comment
        preview = (item.body[:200] + "...") if item.body else ""
        item_type = "Comment"

    embed = discord.Embed(
        title=f"New {item_type} Pending Approval",
        description=preview,
        color=discord.Color.orange()
    )
    embed.add_field(name="Author", value=f"u/{item.author}", inline=True)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    pending_reviews[msg.id] = item


def handle_new_item(item):
    """Check karma → auto approve at 500+, else send to Discord."""
    if item.author is None or item.id in seen_ids:
        return

    seen_ids.add(item.id)

    name = str(item.author)
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    karma = res.data[0]["karma"] if res.data else 0

    if karma >= 500:
        item.mod.approve()
        update_user_karma(item.author, 1)
        print(f"✅ Auto-approved {name} ({karma} karma)")
    else:
        bot.loop.create_task(send_discord_approval(item))


def reddit_polling():
    """Runs in a thread, fetches new comments + posts."""
    print("🌍 Reddit polling started...")
    while True:
        try:
            for comment in subreddit.comments(limit=10):
                handle_new_item(comment)
            for submission in subreddit.new(limit=5):
                handle_new_item(submission)
        except Exception as e:
            print(f"⚠️ Reddit poll error: {e}")
        time.sleep(15)


# ---- Discord events ----
@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    threading.Thread(target=reddit_polling, daemon=True).start()


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    if msg_id not in pending_reviews:
        return

    item = pending_reviews[msg_id]

    if str(reaction.emoji) == "✅":
        item.mod.approve()
        update_user_karma(item.author, 1)  # ✅ only karma on approval
        await reaction.message.channel.send(f"✅ Approved {item.author}")
        del pending_reviews[msg_id]

    elif str(reaction.emoji) == "❌":
        item.mod.remove()
        await reaction.message.channel.send(f"❌ Removed {item.author}'s item")
        del pending_reviews[msg_id]


# ---- Start ----
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)