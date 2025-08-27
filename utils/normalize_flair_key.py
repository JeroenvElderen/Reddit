def _normalize_flair_key(s: str) -> str:
    # strip emoji/non-ASCII, normalize spaces & slash spacing, casefold
    s = (s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"\s*/\s*", " / ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()
