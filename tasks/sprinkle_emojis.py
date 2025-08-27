def sprinkle_emojis(text: str, count: int = 3) -> str:
    """Randomly add naturist emojis to the start/end of a message."""
    chosen = random.sample(NATURIST_EMOJIS, k=min(count, len(NATURIST_EMOJIS)))
    return f"{' '.join(chosen)} {text} {' '.join(chosen)}"
