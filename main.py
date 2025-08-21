import os
import asyncio 
import discord
from discord.ext import commands
import asyncpraw
from supabase import create_client, Client

# ---- Supabase Setup ----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Reddit Setup (asyncpraw) ----
reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

SUBREDDIT_NAME = "PlanetNaturists"

# ---- Discord Setup ----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))  # approval channel

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
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
    ("Naturist Legend", 10000),
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
    "Naturist Legend": "a3f1f8fc-7dd7-11f0-b2c1-227301a06778",
}

# ---- Pending approvals ----
pending_reviews = {}  # discord_msg_id -> reddit item


def get_flair_for_karma(username: str, karma: int) -> str:
    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked


async def update_user_karma(user, points=1):
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
        subreddit = await reddit.subreddit(SUBREDDIT_NAME)
        await subreddit.flair.set(redditor=user, flair_template_id=flair_id)
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
        title = item.title
    else:  # comment
        preview = (item.body[:200] + "...") if item.body else ""
        item_type = "Comment"
        title = None

    embed = discord.Embed(
        title=f"New {item_type} Pending Approval",
        description=preview,
        color=discord.Color.orange(),
    )
    embed.add_field(name="Author", value=f"u/{item.author}", inline=True)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    pending_reviews[msg.id] = item


async def handle_new_item(item):
    """Auto-approve if karma ≥ 500, else send for Discord approval."""
    if item.author is None:
        return

    name = str(item.author)
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    karma = res.data[0]["karma"] if res.data else 0

    if karma >= 500:
        await item.mod.approve()
        await update_user_karma(item.author, 1)
        print(f"✅ Auto-approved {name} ({karma} karma)")
    else:
        await send_discord_approval(item)


async def reddit_stream():
    print("🌍 Reddit stream started...")
    subreddit = await reddit.subreddit(SUBREDDIT_NAME)

    async for comment in subreddit.stream.comments(skip_existing=True):
        await handle_new_item(comment)

    async for submission in subreddit.stream.submissions(skip_existing=True):
        await handle_new_item(submission)


async def daily_rescan():
    print("⏰ Daily rescan...")
    res = supabase.table("user_karma").select("*").execute()
    if not res.data:
        return

    subreddit = await reddit.subreddit(SUBREDDIT_NAME)
    for user in res.data:
        username = user["username"]
        karma = user["karma"]
        correct_flair = get_flair_for_karma(username, karma)

        if user["last_flair"] != correct_flair:
            supabase.table("user_karma").update({"last_flair": correct_flair}).eq("username", username).execute()
            flair_id = flair_templates.get(correct_flair)
            if flair_id:
                await subreddit.flair.set(redditor=username, flair_template_id=flair_id)
                print(f"🔄 Flair updated for {username} → {correct_flair}")


# ---- Discord events ----
@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    # Start Reddit + rescan loops
    bot.loop.create_task(reddit_stream())
    bot.loop.create_task(rescan_loop())


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    if msg_id not in pending_reviews:
        return

    item = pending_reviews[msg_id]

    if str(reaction.emoji) == "✅":
        await item.mod.approve()
        await update_user_karma(item.author, 1)
        await reaction.message.channel.send(f"✅ Approved {item.author}")
        print(f"✅ Approved {item.author}")
        del pending_reviews[msg_id]

    elif str(reaction.emoji) == "❌":
        await item.mod.remove()
        await reaction.message.channel.send(f"❌ Removed {item.author}'s item")
        print(f"❌ Removed {item.author}")
        del pending_reviews[msg_id]


async def rescan_loop():
    while True:
        await daily_rescan()
        await asyncio.sleep(24 * 60 * 60)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
