def cah_enabled_packs():
    try:
        return supabase.table("cah_packs").select("*").eq("enabled",True).execute().data or []
    except:
        return [{"key":CAH_BASE_PACK_KEY,"weight":100}]
