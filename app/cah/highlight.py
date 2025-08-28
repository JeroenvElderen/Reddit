"""Utilities for managing CAH highlight records."""

from app.clients.supabase import supabase


def update_cah_highlight(post_id=None):
    """Store or clear the highlight entry for a CAH round.

    Passing a ``post_id`` stores that ID as the current highlight. Passing
    ``None`` removes any existing highlight entry. After the table mutation,
    a best-effort RPC call is made to refresh any external highlight feed.
    """
    try:
        table = supabase.table("cah_highlight")
        if post_id:
            table.upsert({"post_id": post_id}).execute()
        else:
            table.delete().neq("post_id", "").execute()
    except Exception:
        # Highlight updates are non-critical; ignore failures
        return

    try:
        supabase.rpc("refresh_cah_highlight").execute()
    except Exception:
        pass