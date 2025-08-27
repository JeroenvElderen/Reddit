def submission_has_any_image(sub) -> bool:
    try:
        if getattr(sub, "is_gallery", False):
            return True
        url = (getattr(sub, "url", "") or "").lower()
        if any(url.endswith(ext) for ext in IMAGE_EXTS):
            return True
        if getattr(sub, "post_hint", None) == "image":
            return True
        preview = getattr(sub, "preview", None)
        if isinstance(preview, dict) and preview.get("images"):
            return True
    except Exception:
        pass
    return False
