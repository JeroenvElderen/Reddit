"""
Apply karma changes and update user flair.
"""

from app.clients.supabase import supabase
from app.models.state import subreddit
from app.models.flair_ladder import flair_templates
from app.utils.flair_text import get_flair_for_karma
from app.moderation.badges_observer_award import check_observer_badges
from app.config import BOT_USERNAME, BOT_FLAIR_ID, OWNER_USERNAME


def apply_karma_and_flair(user_or_name, delta: int, allow_negative: bool):
    """Apply delta to karma (floor at 0 if allow_negative=False) and update user flair."""
    if user_or_name is None:
        return 0, 0, "Cover Curious"

    name = str(user_or_name).lower()

    # 🔒 Special case: bot account always keeps fixed flair
    if name == BOT_USERNAME:
        try:
            subreddit.flair.set(redditor=name, flair_template_id=BOT_FLAIR_ID)
            print(f"🤖 Bot account flair forced to ID {BOT_FLAIR_ID}")
        except Exception as e:
            print(f"⚠️ Failed to set bot flair: {e}")
        return 0, 0, "Bot"

    # Owner account -> always Naturist Legend
    if name == OWNER_USERNAME:
        try:
            flair_id = flair_templates.get("Naturist Legend")
            if flair_id:
                subreddit.flair.set(redditor=name, flair_template_id=flair_id)
                print(f"👑 Owner account flair forced to Naturist Legend")
        except Exception as e:
            print(f"⚠️ Failed to set owner flair: {e}")
        return 0, 0, "Naturist Legend"

    # --- Normal user flow ---
    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
    row = res.data[0] if res.data else {}
    old = int(row.get("karma", 0))

    # 🌙 Quiet Observer never goes negative
    if row.get("last_flair") == "Quiet Observer":
        new = max(0, old + delta)
    else:
        new = old + delta
        if not allow_negative:
            new = max(0, new)

    # 🌿 Drop into Quiet Observer if karma falls below 10
    if new < 10 and old >= 10:
        new = 0
        flair = "Quiet Observer"
        flair_id = flair_templates.get(flair)
        if flair_id:
            subreddit.flair.set(redditor=name, flair_template_id=flair_id)
        supabase.table("user_karma").upsert({
            "username": name,
            "karma": new,
            "last_flair": flair
        }).execute()
        print(f"🌙 Quiet Observer → {name} reset to 0 karma and given Quiet Observer flair")
        return old, new, flair

    # 🌅 Exit Quiet Observer once they climb back to 5+
    if row.get("last_flair") == "Quiet Observer" and new >= 5:
        flair = get_flair_for_karma(new)
        flair_id = flair_templates.get(flair)
        if flair_id:
            subreddit.flair.set(redditor=name, flair_template_id=flair_id)
        # increment exit counter
        exits = int(row.get("observer_exits_count", 0)) + 1
        supabase.table("user_karma").upsert({
            "username": name,
            "karma": new,
            "last_flair": flair,
            "observer_exits_count": exits
        }).execute()
        row["observer_exits_count"] = exits
        check_observer_badges(name, row)

        print(f"🌅 {name} climbed out of Quiet Observer → {flair} ({new} karma)")
        return old, new, flair

    # 🪶 Otherwise → normal flair ladder
    flair = get_flair_for_karma(new)
    supabase.table("user_karma").upsert({
        "username": name,
        "karma": new,
        "last_flair": flair
    }).execute()
    flair_id = flair_templates.get(flair)
    if flair_id:
        subreddit.flair.set(redditor=name, flair_template_id=flair_id)
        print(f"🏷️ Flair set for {name} → {flair} ({new} karma)")
    return old, new, flair
