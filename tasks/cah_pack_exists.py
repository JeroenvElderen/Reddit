def _cah_pack_exists(pack_key: str) -> bool:
    try:
        res = supabase.table("cah_packs").select("key").eq("key", pack_key).execute()
        return bool(res.data)
    except Exception:
        return False
