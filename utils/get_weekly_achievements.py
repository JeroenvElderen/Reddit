def get_weekly_achievements():
    """Fetch all badges unlocked in the past 7 days."""
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    res = supabase.table("user_badges").select("*").gte("unlocked_on", week_ago).execute()
    return res.data or []
