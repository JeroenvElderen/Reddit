from app.cah.picker import _fetch_last_winner_block


def format_cah_body(round_number: int, black: str, duration_h: int) -> str:
    """Return the styled body text for a CAH round."""
    winner_block = _fetch_last_winner_block()
    leaf_sep ="🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n\n" if winner_block else ""
    winner_section = f"{winner_block}\n{leaf_sep}" if winner_block else ""
    return f"""
🎲 CAH Round {round_number} — Fill in the Blank!

🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿

🎲 Cards Against Humanity: Naturist Edition

🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿

{winner_section}✨ Black Card of the Day

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
