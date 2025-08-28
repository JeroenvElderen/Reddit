"""
Flair text helpers:
- normalize flair keys
- extract flair text without emoji
- map karma → flair ladder
"""

import re

def _normalize_flair_key(s: str) -> str:
    # strip emoji/non-ASCII, normalize spaces & slash spacing, casefold
    s = (s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"\s*/\s*", " / ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()

def _text_flair_without_emoji(submission) -> str:
    # prefer richtext so emojis are split from text
    rt = getattr(submission, "link_flair_richtext", None) or []
    if isinstance(rt, list) and rt:
        txt = " ".join(p.get("t", "") for p in rt if p.get("e") == "text").strip()
        if txt:
            return txt
    return (getattr(submission, "link_flair_text", "") or "").strip()

def get_flair_for_karma(karma: int) -> str:
    from app.modals.flair_ladder import flair_ladder
    if karma < 0:
        return "Needs Growth"   # special fallback flair
    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked
