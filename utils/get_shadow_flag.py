def get_shadow_flag(username: str) -> str | None:
    try:
        res = supabase.table("shadow_flags").select("note").ilike("username", username).execute()
        if res.data:
            note = (res.data[0].get("note") or "").strip()
            return note or None
    except Exception:
        pass
    return None
