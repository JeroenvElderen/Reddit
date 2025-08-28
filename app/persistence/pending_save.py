"""
Persistence helpers for saving pending reviews to Supabase.
"""

from datetime import datetime
from app.clients.supabase import supabase


# =========================
# Pending reviews persistence (Supabase)
# =========================
def save_pending_review(msg_id: int, item, level: int):
    try:
        supabase.table("pending_reviews").upsert({
            "msg_id": msg_id,
            "item_id": item.id,
            "is_submission": hasattr(item, "title"),
            "created_ts": datetime.utcnow().isoformat(),
            "level": level,
        }).execute()
        print(f"💾 Saved pending review {msg_id} for {item.id}")
    except Exception as e:
        print(f"⚠️ Failed to save pending review {msg_id}: {e}")
