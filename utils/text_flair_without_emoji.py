def _text_flair_without_emoji(submission) -> str:
    # prefer richtext so emojis are split from text
    rt = getattr(submission, "link_flair_richtext", None) or []
    if isinstance(rt, list) and rt:
        txt = " ".join(p.get("t","") for p in rt if p.get("e") == "text").strip()
        if txt:
            return txt
    return (getattr(submission, "link_flair_text", "") or "").strip()
