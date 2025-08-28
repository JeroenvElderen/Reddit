"""
Misc text utilities.
"""

import random

NATURIST_EMOJIS = [
    "🌿", "🌞", "🌊", "✨", "🍂", "❄️", "🌸", "☀️",
    "👣", "🌍", "💚", "🌴", "🏕️", "🧘", "🌳", "🏖️", "🔥"
]

def sprinkle_emojis(text: str, count: int = 3) -> str:
    """Randomly add naturist emojis to the start/end of a message."""
    chosen = random.sample(NATURIST_EMOJIS, k=min(count, len(NATURIST_EMOJIS)))
    return f"{' '.join(chosen)} {text} {' '.join(chosen)}"

def item_text(item) -> str:
    if hasattr(item, "title"):
        return f"{item.title}\n\n{item.selftext or ''}"
    return item.body or ""
