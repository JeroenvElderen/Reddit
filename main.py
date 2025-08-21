import praw
import os
import time
import threading
from supabase import create_client, Client

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

# ---- Flair Templates (your real IDs) ----
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

# ---- Owner Exception ----
OWNER_USERNAME = "SnowDragonFly94"  # 👈 replace with your Reddit username


def get_flair_for_karma(username: str, karma: int) -> str:
    """Pick highest flair unlocked by karma, with owner exception."""
    if username.lower() == OWNER_USERNAME.lower():
        return "Naturist Legend"

    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked


def update_user_karma_from_item(item, points=1):
    """Update user karma only for new posts/comments (+1 each)."""
    if item.author is None:
        return

    name = str(item.author)
    item_id = str(item.fullname)  # unique Reddit ID (t1_xxx for comment, t3_xxx for post)

    # Get current user record
    res = supabase.table("user_karma").select("*").eq("username", name).execute()

    if res.data:
        user_record = res.data[0]
        current_karma = user_record["karma"]
        processed = user_record.get("processed_items", []) or []
    else:
        current_karma = 0
        processed = []

    # Skip if this item was already counted
    if item_id in processed:
        return

    # Add new karma (+1)
    new_karma = max(0, current_karma + points)
    new_flair = get_flair_for_karma(name, new_karma)

    # Update DB (append this item_id to processed list)
    processed.append(item_id)
    supabase.table("user_karma").upsert({
        "username": name,
        "karma": new_karma,
        "last_flair": new_flair,
        "processed_items": processed
    }).execute()

    # Apply flair with template ID
    flair_id = flair_templates.get(new_flair)
    if flair_id:
        subreddit.flair.set(redditor=item.author, flair_template_id=flair_id)
        print(f"✅ Flair set for {name} → {new_flair} ({new_karma} karma)")
    else:
        print(f"⚠️ No flair template found for {new_flair}, skipping flair update.")


def run_bot():
    print("🌍 PlanetNaturists Flair Bot running...")

    # Listen to comments
    for comment in subreddit.stream.comments(skip_existing=True):
        update_user_karma_from_item(comment, 1)

    # Listen to posts
    for submission in subreddit.stream.submissions(skip_existing=True):
        update_user_karma_from_item(submission, 1)


def daily_rescan():
    """Rescan all users in Supabase once every 24h and update flair if needed."""
    print("⏰ Starting daily rescan...")
    res = supabase.table("user_karma").select("*").execute()

    if not res.data:
        print("⚠️ No users found in database.")
        return

    for user in res.data:
        username = user["username"]
        karma = user["karma"]

        correct_flair = get_flair_for_karma(username, karma)

        if user["last_flair"] != correct_flair:
            supabase.table("user_karma").update({
                "last_flair": correct_flair
            }).eq("username", username).execute()

            flair_id = flair_templates.get(correct_flair)
            if flair_id:
                subreddit.flair.set(redditor=username, flair_template_id=flair_id)
                print(f"🔄 Updated flair for {username} → {correct_flair} ({karma} karma)")
            else:
                print(f"⚠️ No flair template found for {correct_flair}")

    print("✅ Daily rescan complete!")


def backfill_existing(limit_posts=100, limit_comments=200):
    """Backfill existing subreddit users into Supabase (+1 per item)."""
    print("📥 Running backfill of existing users...")

    # Backfill posts
    for submission in subreddit.new(limit=limit_posts):
        update_user_karma_from_item(submission, 1)

    # Backfill comments
    for comment in subreddit.comments(limit=limit_comments):
        update_user_karma_from_item(comment, 1)

    print("✅ Backfill complete!")


if __name__ == "__main__":
    # Run one-time backfill on startup
    backfill_existing()

    # Thread for live flair updates
    t1 = threading.Thread(target=run_bot, daemon=True)
    t1.start()

    # Loop for daily rescan
    while True:
        daily_rescan()
        time.sleep(24 * 60 * 60)  # wait 24h