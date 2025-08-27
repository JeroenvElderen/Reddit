def cmd_flairlist(author: str, message):
    flairs = "\n".join([f"{f} — {k} karma" for f, k in flair_ladder])
    message.reply("🏷️ **Flair Ladder** 🌿\n\n" + flairs)
