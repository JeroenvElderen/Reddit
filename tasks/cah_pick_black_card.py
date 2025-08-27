def cah_pick_black_card() -> str:
    active = cah_enabled_packs()
    if not active: active=[{"key":CAH_BASE_PACK_KEY,"weight":100}]
    weighted=[(p["key"],int(p.get("weight",100))) for p in active]
    total=sum(w for _,w in weighted)
    r=random.uniform(0,total)
    upto=0; chosen=weighted[-1][0]
    for key,w in weighted:
        if upto+w>=r: chosen=key; break
        upto+=w
    txt=_random_card_for_pack(chosen)
    if txt: return txt
    txt=_random_card_for_pack(CAH_BASE_PACK_KEY)
    if txt: return txt
    return random.choice([
        "Nothing says naturism like ____.",
        "The best naturist activity is ____."
    ])
