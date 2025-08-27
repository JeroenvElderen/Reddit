def _fetch_last_winner_block() -> str:
    """
    Returns a formatted markdown block announcing the most recent winner,
    with the black card filled in by the winning comment (in quotes).
    """
    try:
        row = (
            supabase.table("cah_rounds")
            .select("*")
            .eq("status", "closed")
            .order("start_ts", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if not row:
            return ""
        r = row[0]
        w_user = r.get("winner_username")
        w_comment = r.get("winner_comment_id")
        w_score = r.get("winner_score")
        black = r.get("black_text")

        if not (w_user and w_comment and black):
            return ""

        # Fetch the comment text
        try:
            c = reddit.comment(id=w_comment)
            comment_text = (c.body or "").strip()
        except Exception:
            comment_text = "____"

        # Fill in the first blank with the quoted comment
        if "____" in black:
            filled = black.replace("____", f"\"{comment_text}\"", 1)
        else:
            filled = f"{black} \"{comment_text}\""

        score_txt = f" (+{w_score})" if isinstance(w_score, int) else ""
        return (
            "🏆 **Previous Round Winner**\n"
            f"- u/{w_user}{score_txt}\n"
            f"**{filled}**\n\n"
        )
    except Exception as e:
        print(f"⚠️ Could not fetch last winner: {e}")
        return ""
