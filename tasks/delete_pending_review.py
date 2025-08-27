def delete_pending_review(msg_id: int):
    try:
        supabase.table("pending_reviews").delete().eq("msg_id", msg_id).execute()
        print(f"🗑️ Deleted pending review {msg_id}")
    except Exception as e:
        print(f"⚠️ Failed to delete pending review {msg_id}: {e}")
