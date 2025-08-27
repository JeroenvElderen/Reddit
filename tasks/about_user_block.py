def about_user_block(name: str):
    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
    sub_karma = int(res.data[0]["karma"]) if res.data else 0
    try:
        rd = reddit.redditor(name)
        created = getattr(rd, "created_utc", None)
        days = int((datetime.now(timezone.utc).timestamp() - created) / 86400) if created else "—"
    except Exception:
        days = "—"
    return sub_karma, days
