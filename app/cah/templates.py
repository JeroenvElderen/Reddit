def format_cah_body(round_number: int, black: str, duration_h: int) -> str:
    """Return the styled body text for a CAH round."""
    return f"""
🎲 CAH Round {round_number} — Fill in the Blank!

🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿

🎲 Cards Against Humanity: Naturist Edition

🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿

✨ Black Card of the Day

{black}

🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿

📝 How to Play

Comment your funniest answer (fill in the blank).  
Upvote your favorites.  
After 24 hours, the top reply wins 🏆  
📅 This round locks after {duration_h}h (and may extend once if there are zero comments).

🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿

Be kind, keep it playful, and body-positive ✨
""".strip()
