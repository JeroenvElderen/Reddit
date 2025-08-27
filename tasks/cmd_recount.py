def cmd_recount(author: str, message):
    """Recalculate location & pillar counters + meta; update badges; reply with a summary."""
    result = backfill_location_counts(author)
    if not result:
        message.reply("⚠️ Sorry, I couldn’t recount your posts right now.")
        return

    loc_counts = result["locations"]
    pillar_counts = result["pillars"]
    total = result["total"]

    def fmt_counts(d: dict) -> str:
        lines = [
            f"- {k.replace('_posts_count','').replace('_',' ').title()}: {v}"
            for k, v in d.items() if v > 0
        ]
        return "\n".join(lines) if lines else "None"

    reply = (
        f"🔄 **Recount complete** for u/{author}\n\n"
        f"**Locations:**\n{fmt_counts(loc_counts)}\n\n"
        f"**Pillars:**\n{fmt_counts(pillar_counts)}\n\n"
        f"**Naturist total posts:** {total}\n\n"
        "I also checked & updated your achievements. 🎉"
    )
    message.reply(reply)
