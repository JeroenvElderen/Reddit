"""Helpers for issuing context warnings on Reddit items."""

from app.persistence.context_warning import add_context_warning

CONTEXT_WARNING_TEMPLATES = (
    (
        "⚠️ Warning {count}/{total} – Thanks for your contribution! 🙌\n"
        "📝 To help everyone understand and discuss your posts, please add more context—like your experiences 🎒, background 🗺️, or relevant examples 📚—in future submissions.\n"
        "🚫 Posts without enough context may be removed.\n"
        "🙏 Thanks for your cooperation! 😊"
    ),
    (
        "⚠️ Warning {count}/{total} – We still need more details. 🧐\n"
        "📝 Please include helpful context such as your background, thought process, or supporting examples so the community can follow along.\n"
        "🚫 Posts without clear context might be removed, so a few extra sentences go a long way.\n"
        "🙏 We appreciate your help in keeping conversations informative!"
    ),
    (
        "⚠️ Warning {count}/{total} – Final reminder! ⏰\n"
        "📝 Future posts must include meaningful context (experiences, background, examples) so everyone understands the discussion.\n"
        "🚫 Posts without context may be removed automatically.\n"
        "🙏 Thanks for understanding and supporting the community!"
    ),
)


def _build_warning_message(count: int, auto_removed: bool) -> str:
    """Return the context warning message for a given count."""

    if not CONTEXT_WARNING_TEMPLATES:
        raise ValueError("No context warning templates configured.")

    index = min(max(count, 1), len(CONTEXT_WARNING_TEMPLATES)) - 1
    display_count = min(max(count, 1), len(CONTEXT_WARNING_TEMPLATES))
    total = len(CONTEXT_WARNING_TEMPLATES)
    message = CONTEXT_WARNING_TEMPLATES[index].format(count=display_count, total=total)
    if auto_removed:
        message += "\n\nThis post was removed automatically after multiple warnings."
    return message



def issue_context_warning(item, auto_removed: bool = False) -> int:
    """Reply to the item with the context warning and record it.

    Returns the new warning count for the author.
    """
    author_name = str(item.author)

    try:
        count = add_context_warning(author_name)
    except Exception as e:  # pragma: no cover - external service failure
        print(f"⚠️ Failed to record context warning for {author_name}: {e}")
        count = 1

    message = _build_warning_message(count, auto_removed)

    try:
        item.reply(message)
    except Exception as e:
        print(f"⚠️ Failed to reply with context warning: {e}")
    author_name = str(item.author)

    return count