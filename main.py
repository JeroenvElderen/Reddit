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

# ---- Owner ----
OWNER_USERNAME = "SnowDragonFly94"
BOT_USERNAME = "PlanetNaturistsBot"

# Pending reviews dict (item_id -> item object)
pending_reviews = {}


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


def update_user_karma(user, points=1):
    """Increment user karma and update flair."""
    if user is None:
        return

    name = str(user)

    # Get current user record
    res = supabase.table("user_karma").select("*").eq("username", name).execute()

    if res.data:
        current_karma = res.data[0]["karma"]
    else:
        current_karma = 0

    new_karma = max(0, current_karma + points)
    new_flair = get_flair_for_karma(name, new_karma)

    # Save new karma + flair
    supabase.table("user_karma").upsert({
        "username": name,
        "karma": new_karma,
        "last_flair": new_flair
    }).execute()

    # Apply flair with template ID
    flair_id = flair_templates.get(new_flair)
    if flair_id:
        subreddit.flair.set(redditor=user, flair_template_id=flair_id)
        print(f"✅ Flair set for {name} → {new_flair} ({new_karma} karma)")
    else:
        print(f"⚠️ No flair template found for {new_flair}, skipping flair update.")


def handle_new_item(item):
    """Handle a new post/comment with approval logic."""
    if item.author is None:
        return

    username = str(item.author)

    # Owner always auto-approved
    if username.lower() == OWNER_USERNAME.lower():
        item.mod.approve()
        update_user_karma(item.author, 1)
        return

    # Get karma
    res = supabase.table("user_karma").select("*").eq("username", username).execute()
    karma = res.data[0]["karma"] if res.data else 0

    if karma < 500:
        # --- Build preview ---
        if hasattr(item, "title"):  # it's a post
            preview = f"**Post Title:** {item.title}\n\n"
            if hasattr(item, "selftext") and item.selftext:
                preview += f"{item.selftext[:200]}..."
        else:  # it's a comment
            preview = f"**Comment:** {item.body[:200]}..."

        # --- Approve/Reject links with item_id ---
        approve_link = f"https://reddit.com/message/compose/?to={BOT_USERNAME}&subject=Approval&message=approve:{item.id}"
        reject_link = f"https://reddit.com/message/compose/?to={BOT_USERNAME}&subject=Approval&message=reject:{item.id}"

        msg = f"""
New {'Post' if hasattr(item, 'title') else 'Comment'} in r/{SUBREDDIT_NAME}
Author: u/{username}
Flair: {get_flair_for_karma(username, karma)} ({karma} karma)
Link: https://reddit.com{item.permalink}

--- Preview ---
{preview}

[Approve]({approve_link}) | [Reject]({reject_link})
"""
        reddit.redditor(OWNER_USERNAME).message("Approval Needed", msg)
        pending_reviews[item.id] = item
        print(f"⏳ Approval requested for {username} ({karma} karma)")
    else:
        # Auto approve
        item.mod.approve()
        update_user_karma(item.author, 1)


def handle_owner_replies():
    """Listen for owner's replies to approve/reject pending items."""
    for message in reddit.inbox.stream(skip_existing=True):
        if str(message.author).lower() == OWNER_USERNAME.lower():
            body = message.body.strip().lower()
            if body.startswith("approve:") or body.startswith("reject:"):
                action, item_id = body.split(":", 1)

                if item_id not in pending_reviews:
                    print(f"⚠️ No pending item found with id {item_id}")
                    message.mark_read()
                    continue

                item = pending_reviews.pop(item_id)

                if action == "approve":
                    item.mod.approve()
                    update_user_karma(item.author, 1)
                    print(f"👍 Approved {item.author} ({item_id})")
                else:
                    item.mod.remove()
                    print(f"❌ Rejected {item.author} ({item_id})")

                message.mark_read()


def run_bot():
    print("🌍 PlanetNaturists Flair Bot running...")

    # Comments
    for comment in subreddit.stream.comments(skip_existing=True):
        handle_new_item(comment)

    # Posts
    for submission in subreddit.stream.submissions(skip_existing=True):
        handle_new_item(submission)


def daily_rescan():
    """Rescan all users and update flair if needed."""
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

    print("✅ Daily rescan complete!")


def backfill_existing(limit_posts=100, limit_comments=200):
    print("📥 Running backfill of existing users...")
    for submission in subreddit.new(limit=limit_posts):
        handle_new_item(submission)
    for comment in subreddit.comments(limit=limit_comments):
        handle_new_item(comment)
    print("✅ Backfill complete!")


if __name__ == "__main__":
    # One-time backfill
    backfill_existing()

    # Threads: one for items, one for approvals
    t1 = threading.Thread(target=run_bot, daemon=True)
    t2 = threading.Thread(target=handle_owner_replies, daemon=True)
    t1.start()
    t2.start()

    # Daily rescan loop
    while True:
        daily_rescan()
        time.sleep(24 * 60 * 60)
