def _get_permalink_from_embed(msg: discord.Message) -> str | None:
    try:
        emb = msg.embeds[0] if msg.embeds else None
        if not emb or not emb.fields:
            return None
        for f in emb.fields:
            if f.name.lower() == "link":
                return (f.value or "").strip()
    except Exception:
        pass
    return None
