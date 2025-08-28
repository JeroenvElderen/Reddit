"""
Helpers for Cards Against Humanity packs and random card selection.
"""

import random
from app.clients.supabase import supabase
from app.clients.reddit_bot import reddit
from app.config import CAH_BASE_PACK_KEY


# =========================
# CAH Packs and Cards
# =========================
def cah_enabled_packs():
    try:
        return supabase.table("cah_packs").select("*").eq("enabled", True).execute().data or []
    except Exception:
        return [{"key": CAH_BASE_PACK_KEY, "weight": 100}]


# =========================
# Last winner helper
# =========================
def _fetch_last_winner_block() -> str:
    """
    Returns a formatted markdown block announcing the most recent winner,
    with the black card filled in by the winning comment (in quotes).
    """
    try:
        row = (
            supabase.table("cah_rounds")
            .select("*")
            .eq("status", "closed")
            .order("start_ts", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if not row:
            return ""
        r = row[0]
        w_user = r.get("winner_username")
        w_comment = r.get("winner_comment_id")
        w_score = r.get("winner_score")
        black = r.get("black_text")

        if not (w_user and w_comment and black):
            return ""

        # Fetch the comment text
        try:
            c = reddit.comment(id=w_comment)
            comment_text = (c.body or "").strip()
        except Exception:
            comment_text = "____"

        # Fill in the first blank with the quoted comment
        if "____" in black:
            filled = black.replace("____", f"\"{comment_text}\"", 1)
        else:
            filled = f"{black} \"{comment_text}\""

        score_txt = f" (+{w_score})" if isinstance(w_score, int) else ""
        return (
            "🏆 **Previous Round Winner**\n"
            f"- u/{w_user}{score_txt}\n"
            f"**{filled}**\n\n"
        )
    except Exception as e:
        print(f"⚠️ Could not fetch last winner: {e}")
        return ""


# =========================
# Random black card picker
# =========================
def _random_card_for_pack(key: str) -> str | None:
    try:
        cnt = (
            supabase.table("cah_black_cards")
            .select("id", count="exact")
            .eq("pack_key", key)
            .limit(1)
            .execute()
        )
        total = int(cnt.count or 0)
        if total <= 0:
            return None
        offset = random.randint(0, total - 1)
        row = (
            supabase.table("cah_black_cards")
            .select("text")
            .eq("pack_key", key)
            .range(offset, offset)
            .execute()
            .data
        )
        if row:
            return row[0]["text"]
    except Exception:
        pass
    return None


# =========================
# Main random black card picker with fallback
# =========================
def cah_pick_black_card() -> str:
    active = cah_enabled_packs()
    if not active:
        active = [{"key": CAH_BASE_PACK_KEY, "weight": 100}]
    weighted = [(p["key"], int(p.get("weight", 100))) for p in active]
    total = sum(w for _, w in weighted)
    r = random.uniform(0, total)
    upto = 0
    chosen = weighted[-1][0]
    for key, w in weighted:
        if upto + w >= r:
            chosen = key
            break
        upto += w
    txt = _random_card_for_pack(chosen)
    if txt:
        return txt
    txt = _random_card_for_pack(CAH_BASE_PACK_KEY)
    if txt:
        return txt
    return random.choice([
        "Nothing says naturism like ____.",
        "The best naturist activity is ____."
    ])
