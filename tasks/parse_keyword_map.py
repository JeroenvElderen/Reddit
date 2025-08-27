def parse_keyword_map(raw: str) -> dict[str, str]:
    out = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        k, v = pair.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out
