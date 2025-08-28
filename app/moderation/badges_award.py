"""
Generic badge award helpers.
"""

from app.clients.supabase import supabase

# =========================
# Badge level label
# =========================
def badge_level_label(level: int, max_level: int) -> str:
    """Return Lv.MAX if level is the last one, otherwise Lv.{n}"""
    return "Lv.MAX" if level == max_level else f"Lv.{level}"

# =========================
# Badge existence check
# =========================
def _badge_exists(username: str, badge_name: str) -> bool:
    """Check if this exact badge already exists in Supabase."""
    try:
        res = (
            supabase.table("user_badges")
            .select("badge")
            .eq("username", username)
            .eq("badge", badge_name)
            .execute()
        )
        return bool(res.data)
    except Exception:
        return False
