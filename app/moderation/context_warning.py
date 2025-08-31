"""Helpers for issuing context warnings on Reddit items."""

from app.persistence.context_warnings import add_context_warning

CONTEXT_WARNING_MESSAGE = (
    "⚠️ Hey there! Thanks for your contribution! 🙌\n"
    "📝 To help everyone understand and discuss your posts, please add more context—like your experiences 🎒, background 🗺️, or relevant examples 📚—in future submissions.\n"
    "🚫 Posts without enough context may be removed.\n"
    "🙏 Thanks for your cooperation! 😊"
)


def issue_context_warning(item, auto_removed: bool = False) -> int:
    """Reply to the item with the context warning and record it.

    Returns the new warning count for the author.
    """
    message = CONTEXT_WARNING_MESSAGE
    if auto_removed:
        message += "\n\nThis post was removed automatically after multiple warnings."
    try:
        item.reply(message)
    except Exception as e:
        print(f"⚠️ Failed to reply with context warning: {e}")
    author_name = str(item.author)
    return add_context_warning(author_name)