def is_native_reddit_image(sub) -> bool:
    if not hasattr(sub, "title"):
        return False
    if getattr(sub, "is_gallery", False):
        md = getattr(sub, "media_metadata", {}) or {}
        for v in md.values():
            if v.get("e") == "Image":
                src = v.get("s", {}) or {}
                u = src.get("u") or src.get("gif") or ""
                if any(_host(u).endswith(h) for h in REDDIT_IMAGE_HOSTS):
                    return True
        return False
    url = (getattr(sub, "url", "") or "")
    if getattr(sub, "post_hint", None) == "image" and url:
        if any(_host(url).endswith(h) for h in REDDIT_IMAGE_HOSTS):
            return True
    preview = getattr(sub, "preview", None)
    if isinstance(preview, dict):
        imgs = preview.get("images") or []
        for img in imgs:
            src_url = (img.get("source", {}) or {}).get("url", "")
            if any(_host(src_url).endswith(h) for h in REDDIT_IMAGE_HOSTS):
                return True
    return False
