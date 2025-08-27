def _badge_exists(username: str, badge_name: str) -> bool:
    """Check if this exact badge already exists in Supabase."""
    try:
        res = supabase.table("user_badges") \
            .select("badge") \
            .eq("username", username) \
            .eq("badge", badge_name) \
            .execute()
        return bool(res.data)
    except Exception:
        return False
