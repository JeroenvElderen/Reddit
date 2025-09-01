"""
Apply karma changes and update user flair.
"""

from app.clients.supabase import supabase
from app.models.state import subreddit
from app.models.flair_ladder import flair_templates
from app.utils.flair_text import get_flair_for_karma
from app.moderation.badges_observer_award import check_observer_badges
from app.config import BOT_USERNAME, BOT_FLAIR_ID, FIXED_FLAIRS


def apply_karma_and_flair(user_or_name, delta: int, allow_negative: bool):
    """Apply delta to karma (floor at 0 if allow_negative=False) and update user flair."""
    if user_or_name is None:
        return 0, 0, "Cover Curious"

    name = str(user_or_name)
    name_lower = name.lower()

    # 🔒 Special case: bot account always keeps fixed flair
    if name_lower == BOT_USERNAME:
        try:
            subreddit.flair.set(redditor=name, flair_template_id=BOT_FLAIR_ID)
            print(f"🤖 Bot account flair forced to ID {BOT_FLAIR_ID}")
        except Exception as e:
            print(f"⚠️ Failed to set bot flair: {e}")
        return 0, 0, "Bot"

    # --- fetch current karma row ---
    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
    row = res.data[0] if res.data else {}
    stored_username = row.get("username")
    old = int(row.get("karma", 0))

    def _save_user(payload):
        payload["username"] = name
        table = supabase.table("user_karma")
        if stored_username:
            table.update(payload).eq("username", stored_username).execute()
        else:
            table.insert(payload).execute()
    
    # --- Fixed flairs -> karma only, no flair changes --- #
    if name_lower in FIXED_FLAIRS:
        new = old + delta
        if not allow_negative:
            new = max(0, new)
        computed_flair = get_flair_for_karma(new)
        _save_user({"karma": new, "last_flair": computed_flair})
        flair = FIXED_FLAIRS[name_lower]
        try:
            flair_id = flair_templates.get(flair)
            if flair_id:
                subreddit.flair.set(redditor=name, flair_template_id=flair_id)
                print(f"👤 Fixed flair retained for {name} → {flair} ({new} karma)")
        except Exception as e:
            print(f"⚠️ Failed to set fixed flair for {name}: {e}")
        return old, new, flair

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
        _save_user({"karma": new, "last_flair": flair})
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
        _save_user({"karma": new, "last_flair": flair, "observer_exist_count": exits})
        row["observer_exits_count"] = exits
        check_observer_badges(name, row)

        print(f"🌅 {name} climbed out of Quiet Observer → {flair} ({new} karma)")
        return old, new, flair

    # 🪶 Otherwise → normal flair ladder
    flair = get_flair_for_karma(new)
    _save_user({"karma": new, "last_flair": flair})
    flair_id = flair_templates.get(flair)
    if flair_id:
        subreddit.flair.set(redditor=name, flair_template_id=flair_id)
        print(f"🏷️ Flair set for {name} → {flair} ({new} karma)")
    return old, new, flair
