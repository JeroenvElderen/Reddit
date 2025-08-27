def _random_card_for_pack(key:str) -> str|None:
    try:
        cnt = supabase.table("cah_black_cards").select("id",count="exact").eq("pack_key",key).limit(1).execute()
        total = int(cnt.count or 0)
        if total<=0: return None
        offset = random.randint(0,total-1)
        row = supabase.table("cah_black_cards").select("text").eq("pack_key",key).range(offset,offset).execute().data
        if row: return row[0]["text"]
    except: pass
    return None
