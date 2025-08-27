def get_user_stats(username: str):
    """Fetch stats for a given user from Supabase."""
    try:
        res = supabase.table("user_karma").select("*").ilike("username", username).execute()
        if not res.data:
            return None
        row = res.data[0]
        return {
            "karma": int(row.get("karma", 0)),
            "flair": row.get("last_flair", "Needs Growth"),
            "streak": int(row.get("streak_days", 0)),
            "last_post": row.get("last_approved_date"),
        }
    except Exception as e:
        print(f"⚠️ Stats lookup failed for {username}: {e}")
        return None
