"""
Persistence helpers for storing and loading processed Reddit IDs in Supabase.
"""

from app.clients.supabase import supabase

_TABLE = "seen_reddit_ids"


def load_seen_ids() -> set[str]:
    """Return a set of Reddit item IDs stored in Supabase."""
    try:
        rows = supabase.table(_TABLE).select("id").execute().data or []
        return {row["id"] for row in rows}
    except Exception as e:
        print(f"⚠️ Failed to load seen ids: {e}")
        return set()


def save_seen_id(item_id: str, kind: str) -> None:
    """Persist a Reddit item ID and its type to Supabase."""
    try:
        supabase.table(_TABLE).upsert({"id": item_id, "kind": kind}).execute()
    except Exception as e:
        print(f"⚠️ Failed to save seen id {item_id}: {e}")

