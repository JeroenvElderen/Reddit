"""Utility helpers for managing the CAH highlight feed."""

from __future__ import annotations

from app.clients.supabase import supabase

HIGHLIGHT_TABLE = "highlight_feed"
STATE_TABLE = "cah_state"
STATE_KEY = "active_highlight_post_id"


def update_cah_highlight(new_post_id: str | None) -> None:
    """Update the highlight feed enty for CAH.

    Removes any previously highlighted CAH post (stored in ``STATE_TABLE``). If
    ``new_post_id`` is provided, it is added to the highlight feed with an
    ``event`` tag and persisted for later cleanup. If ``new_post_id`` is
    ``None``, any existing highlight entry is simply cleared.
    """
    old_post_id: str | None = None

    try:
        row = (
            supabase.table(STATE_TABLE)
            .select("value")
            .eq("key", STATE_KEY)
            .execute()
            .data
            or []
        )
        if row:
            old_post_id = row[0].get("value")
    except Exception:
        old_post_id = None

    if old_post_id:
        try:
            supabase.table(HIGHLIGHT_TABLE).delete().eq("post_id", old_post_id).execute()
        except Exception:
            pass

    if new_post_id:
        try:
            supabase.table(HIGHLIGHT_TABLE).upsert({"post_id": new_post_id, "tag": "event"}).execute()
        except Exception:
            pass
        
        try:
            supabase.table(STATE_TABLE).upsert({"key": STATE_KEY, "value": new_post_id}).execute()
        except Exception:
            pass
    else:
        try:
            supabase.table(STATE_TABLE).delete().eq("key", STATE_KEY).execute()
        except Exception:
            pass
