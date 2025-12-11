"""Reminder loop disabled (kept for compatibility)."""


async def cleanup_old_reminders():
    """No-op cleanup since reminder loop is disabled."""
    return None


def reminder_loop():
    """No-op reminder loop stub."""
    print("⏸️ Reminder loop is disabled; not starting reminders.")
    return None