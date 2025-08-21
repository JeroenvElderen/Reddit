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

# ---- Owner ----
OWNER_USERNAME = "SnowDragonFly94"

# ---- Pending Approvals ----
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
    name = str(user)

    res = supabase.table("user_karma").select("*").eq("username", name).execute()
    if res.data:
        new_karma = max(0, res.data[0]["karma"] + points)
    else:
        new_karma = max(0, points)

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


def handle_new_item(item):
    """Decide whether to auto-approve or send for owner approval."""
    if item.author is None:
        return
    username = str(item.author)

    # Owner always auto-approved
    if username.lower() == OWNER_USERNAME.lower():
        update_user_karma(item.author, 1)
        return

    # Get user karma
    res = supabase.table("user_karma").select("*").eq("username", username).execute()
    karma = res.data[0]["karma"] if res.data else 0

    if karma < 500:
        # Send PM to owner for approval
        msg = f"""
New {'Post' if hasattr(item, 'title') else 'Comment'} in r/{SUBREDDIT_NAME}
Author: u/{username}
Flair: {get_flair_for_karma(username, karma)} ({karma} karma)
Link: https://reddit.com{item.permalink}

Reply "approve {item.id}" to approve and +1 karma.
Reply "reject {item.id}" to remove.
"""
        reddit.redditor(OWNER_USERNAME).message("Approval Needed", msg)
        pending_reviews[item.id] = item
        print(f"⏳ Approval requested from owner for {username} ({karma} karma)")
    else:
        # Auto approve and update
        item.mod.approve()
        update_user_karma(item.author, 1)


def monitor_owner_replies():
    """Listen to inbox for owner replies (approve/reject)."""
    for message in reddit.inbox.stream(skip_existing=True):
        if str(message.author).lower() != OWNER_USERNAME.lower():
            continue

        parts = message.body.strip().lower().split()
        if len(parts) < 2:
            continue

        action, item_id = parts[0], parts[1]
        if item_id not in pending_reviews:
            continue

        item = pending_reviews.pop(item_id)

        if action == "approve":
            item.mod.approve()
            update_user_karma(item.author, 1)
            print(f"✅ Owner approved {item_id} from {item.author}")
        elif action == "reject":
            item.mod.remove()
            print(f"❌ Owner rejected {item_id} from {item.author}")

        message.mark_read()


def run_bot():
    print("🌍 PlanetNaturists Flair Bot running...")

    # Listen to comments
    for comment in subreddit.stream.comments(skip_existing=True):
        handle_new_item(comment)

    # Listen to posts
    for submission in subreddit.stream.submissions(skip_existing=True):
        handle_new_item(submission)


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
    print("✅ Daily rescan complete!")


if __name__ == "__main__":
    # Thread for live updates
    t1 = threading.Thread(target=run_bot, daemon=True)
    t1.start()

    # Thread for owner inbox monitoring
    t2 = threading.Thread(target=monitor_owner_replies, daemon=True)
    t2.start()

    # Daily rescan loop
    while True:
        daily_rescan()
        time.sleep(24 * 60 * 60)
