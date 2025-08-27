def already_moderated(item) -> bool:
    if getattr(item, "approved_by", None):
        return True
    if getattr(item, "removed_by_category", None) is not None:
        return True
    if getattr(item, "banned_by", None):
        return True
    if getattr(item, "author", None) is None:
        return True
    return False
