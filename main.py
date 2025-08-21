import os
import time
import threading
import asyncio
import secrets
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
pending_reviews = {}    # 1st-phase review: discord_msg_id -> reddit item
reason_prompts = {}     # 2nd-phase reason selection: discord_msg_id -> {author_name, permalink, item_type}
seen_ids = set()        # processed reddit item IDs

# ---- Fixed reason choices (emoji -> text) ----
REJECT_REASONS = {
    "🚫": "Spam or prohibited promotion",
    "⚠️": "Self-promotion outside allowed threads",
    "📝": "Low-effort / insufficient detail",
    "🧩": "Off-topic for this subreddit",
    "🔒": "Broke a subreddit rule",
    "❓": "__custom__",   # triggers typed custom reason
}


def get_flair_for_karma(karma: int) -> str:
    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked


def update_user_karma(user, points=1, allow_negative=True):
    """
    Increment/decrement karma & update flair in Supabase + Reddit.
    Returns (old_karma, new_karma, new_flair).
    - points: +1 on approve, -1 on manual reject
    - allow_negative: False for auto-approvals, True for manual rejects
    """
    if user is None:
        return 0, 0, "Cover Curious"

    name = str(user)
    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    old_karma = res.data[0]["karma"] if res.data else 0

    new_karma = old_karma + points
    if not allow_negative:
        new_karma = max(0, new_karma)

    new_flair = get_flair_for_karma(new_karma)

    supabase.table("user_karma").upsert({
        "username": name,
        "karma": new_karma,
        "last_flair": new_flair
    }).execute()

    flair_id = flair_templates.get(new_flair)
    if flair_id:
        subreddit.flair.set(redditor=user, flair_template_id=flair_id)
        print(f"🏷️ Flair set for {name} → {new_flair} ({new_karma} karma)")

    return old_karma, new_karma, new_flair


async def send_discord_approval(item):
    """Send new Reddit item to Discord for approval (full-ish content)."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("⚠️ Discord channel not found")
        return

    if hasattr(item, "title"):  # Post
        content = f"**{item.title}**\n\n{item.selftext or ''}"
        item_type = "Post"
    else:  # Comment
        content = item.body or ""
        item_type = "Comment"

    embed = discord.Embed(
        title=f"New {item_type} Pending Approval",
        description=(content[:4000] + ("... (truncated)" if len(content) > 4000 else "")),
        color=discord.Color.orange()
    )
    embed.add_field(name="Author", value=f"u/{item.author}", inline=True)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    pending_reviews[msg.id] = item
    print(f"📨 Sent {item_type} by u/{item.author} to Discord for review.")


async def send_discord_auto_log(item, old_k, new_k, flair):
    """Log auto-approvals to Discord so you can see them."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return

    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    embed = discord.Embed(
        title=f"Auto-approved {item_type}",
        description=(content[:1000] + ("... (truncated)" if len(content) > 1000 else "")),
        color=discord.Color.green()
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{item.author}", inline=True)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k}", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)

    await channel.send(embed=embed)


def already_moderated(item) -> bool:
    """Robust moderation check across PRAW versions."""
    if getattr(item, "approved_by", None):
        return True
    if getattr(item, "removed_by_category", None) is not None:
        return True
    if getattr(item, "banned_by", None):
        return True
    if getattr(item, "author", None) is None:
        return True
    return False


def handle_new_item(item):
    """
    Only process new, not-yet-moderated items.
    ≥500 karma => auto-approve (+1). Otherwise send to Discord for review.
    """
    if item.author is None or item.id in seen_ids:
        return

    if already_moderated(item):
        print(f"⏩ Skipping {item.id} (already moderated)")
        seen_ids.add(item.id)
        return

    seen_ids.add(item.id)

    author_name = str(item.author)
    res = supabase.table("user_karma").select("*").eq("username", author_name).execute()
    karma = res.data[0]["karma"] if res.data else 0

    if karma >= 500:
        item.mod.approve()
        old_k, new_k, flair = update_user_karma(item.author, +1, allow_negative=False)
        print(f"✅ Auto-approved u/{author_name} ({old_k} → {new_k} karma, flair: {flair})")
        asyncio.run_coroutine_threadsafe(
            send_discord_auto_log(item, old_k, new_k, flair),
            bot.loop
        )
    else:
        print(f"📨 Queueing u/{author_name} ({karma} karma) for manual review in Discord")
        asyncio.run_coroutine_threadsafe(send_discord_approval(item), bot.loop)


def reddit_polling():
    """Runs in a thread, fetches new comments + posts with PRAW (sync)."""
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


async def send_reason_dm(author_name: str, item_type: str, permalink: str, reason: str):
    """DM the Reddit user with the chosen/custom reason."""
    subject = f"Your {item_type.lower()} was removed in r/{SUBREDDIT_NAME}"
    body = (
        f"Hi u/{author_name},\n\n"
        f"Your {item_type.lower()} was removed by the moderators of r/{SUBREDDIT_NAME}.\n\n"
        f"**Reason:** {reason}\n\n"
        f"Link: {permalink}\n\n"
        f"If you have questions, feel free to reply to this message."
    )
    try:
        reddit.redditor(author_name).message(subject, body)
        print(f"📨 DM sent to u/{author_name} with reason.")
    except Exception as e:
        print(f"⚠️ Failed to DM u/{author_name}: {e}")


async def prompt_reason_menu(ctx_channel: discord.TextChannel, author_name: str, permalink: str, item_type: str):
    """Post a second message with emoji reasons; support ❓ for custom."""
    embed = discord.Embed(
        title="Select a rejection reason",
        description=(
            "React with one of the following:\n"
            "🚫 Spam\n"
            "⚠️ Self-promo outside allowed threads\n"
            "📝 Low-effort / insufficient detail\n"
            "🧩 Off-topic\n"
            "🔒 Broke a subreddit rule\n"
            "❓ Other (you will be prompted to type a custom reason)"
        ),
        color=discord.Color.red()
    )
    reason_msg = await ctx_channel.send(embed=embed)
    for e in REJECT_REASONS.keys():
        await reason_msg.add_reaction(e)

    reason_prompts[reason_msg.id] = {
        "author_name": author_name,
        "permalink": permalink,
        "item_type": item_type
    }


# ---- Discord events ----
@bot.event
async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    threading.Thread(target=reddit_polling, daemon=True).start()


@bot.event
async def on_reaction_add(reaction, user):
    """Handle both phases: review (✅/❌) and reason selection."""
    if user.bot:
        return

    msg_id = reaction.message.id

    # --- Phase 1: initial review card ---
    if msg_id in pending_reviews:
        item = pending_reviews[msg_id]
        author_name = str(item.author)

        res = supabase.table("user_karma").select("*").eq("username", author_name).execute()
        current_karma = res.data[0]["karma"] if res.data else 0

        if str(reaction.emoji) == "✅":
            item.mod.approve()
            old_k, new_k, flair = update_user_karma(item.author, +1, allow_negative=False)
            await reaction.message.channel.send(
                f"✅ Approved u/{author_name} ({old_k} → {new_k} karma, flair: {flair})"
            )
            await reaction.message.delete()
            del pending_reviews[msg_id]
            print(f"✅ Approved u/{author_name} ({old_k} → {new_k} karma, flair: {flair})")

        elif str(reaction.emoji) == "❌":
            # Remove on Reddit and -1 karma (manual reject)
            item.mod.remove()
            old_k, new_k, flair = update_user_karma(item.author, -1, allow_negative=True)
            await reaction.message.channel.send(
                f"❌ Removed u/{author_name}'s item ({old_k} → {new_k} karma, flair: {flair})"
            )
            await reaction.message.delete()
            del pending_reviews[msg_id]
            print(f"❌ Removed u/{author_name}'s item ({old_k} → {new_k} karma, flair: {flair})")

            # Post reason menu (second step)
            permalink = f"https://reddit.com{item.permalink}"
            item_type = "Post" if hasattr(item, "title") else "Comment"
            await prompt_reason_menu(reaction.message.channel, author_name, permalink, item_type)

        return

    # --- Phase 2: reason-selection message ---
    if msg_id in reason_prompts:
        info = reason_prompts[msg_id]
        author_name = info["author_name"]
        permalink = info["permalink"]
        item_type = info["item_type"]
        emoji = str(reaction.emoji)

        # Only the first reacting moderator should trigger
        # (Optional: restrict to users with Manage Messages permission)
        if emoji not in REJECT_REASONS:
            return

        # Handle preset reasons
        if REJECT_REASONS[emoji] != "__custom__":
            reason_text = REJECT_REASONS[emoji]
            await send_reason_dm(author_name, item_type, permalink, reason_text)
            await reaction.message.channel.send(f"📨 Notified u/{author_name}: {reason_text}")
            try:
                await reaction.message.delete()
            except Exception:
                pass
            del reason_prompts[msg_id]
            return

        # Handle custom reason via next message from the reacting user
        prompt = await reaction.message.channel.send(
            f"✍️ {user.mention} please type your custom reason within 2 minutes."
        )

        def check(m: discord.Message):
            return (
                m.author.id == user.id and
                m.channel.id == reaction.message.channel.id and
                len(m.content.strip()) > 0
            )

        try:
            reply_msg = await bot.wait_for("message", timeout=120.0, check=check)
            reason_text = reply_msg.content.strip()
            await send_reason_dm(author_name, item_type, permalink, reason_text)
            await reaction.message.channel.send(f"📨 Notified u/{author_name}: {reason_text}")
            try:
                await reaction.message.delete()
                await prompt.delete()
            except Exception:
                pass
            del reason_prompts[msg_id]
        except asyncio.TimeoutError:
            await reaction.message.channel.send("⌛ Custom reason timed out. No DM sent.")
            try:
                await prompt.delete()
            except Exception:
                pass
        return


# ---- Start ----
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)