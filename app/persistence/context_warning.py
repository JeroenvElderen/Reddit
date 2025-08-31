"""Supabase helpers for tracking context warnings per user."""

from app.clients.supabase import supabase


def get_context_warning_count(username: str) -> int:
    """Return current context-warning count for a user."""
    res = (
        supabase.table("user_karma")
        .select("context_warnings")
        .ilike("username", username)
        .execute()
    )
    if not res.data:
        return 0
    return int(res.data[0].get("context_warnings") or 0)


def add_context_warning(username: str) -> int:
    """Increment and persist context warning count; return new count."""
    count = get_context_warning_count(username) + 1
    supabase.table("user_karma").upsert(
        {"username": username, "context_warnings": count}
    ).execute()
    return count