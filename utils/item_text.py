def item_text(item) -> str:
    if hasattr(item, "title"):
        return f"{item.title}\n\n{item.selftext or ''}"
    return item.body or ""
