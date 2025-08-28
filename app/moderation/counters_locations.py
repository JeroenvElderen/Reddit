"""
Location flair counters.
"""

from app.clients.supabase import supabase
from app.models.badges_location import FLAIR_TO_FIELD_NORM
from app.utils.flair_text import _normalize_flair_key, _text_flair_without_emoji
from app.moderation.badges_location_award import check_and_award_badge


def increment_location_counter(submission, author_name: str):
    flair_text = _text_flair_without_emoji(submission)
    key = _normalize_flair_key(flair_text)
    field = FLAIR_TO_FIELD_NORM.get(key)
    if not field:
        print(f"ℹ️ Unmapped flair: '{flair_text}' (norm='{key}') on {submission.id}")
        return

    try:
        res = supabase.table("user_karma").select("*").ilike("username", author_name).execute()
        row = res.data[0] if res.data else {}
        current = int(row.get(field, 0))
        new_val = current + 1
        supabase.table("user_karma").upsert({"username": author_name, field: new_val}).execute()
        print(f"🏷️ Incremented {field} for u/{author_name} → {new_val}")
        check_and_award_badge(author_name, field, new_val)
    except Exception as e:
        print(f"⚠️ Failed to increment location counter: {e}")
