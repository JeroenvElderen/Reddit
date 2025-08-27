def get_last_approved_item(username: str):
    """Return (text, is_post) of the last approved post/comment, or (None, None)."""
    try:
        redditor = reddit.redditor(username)  # use bot session to check history

        # Check posts first
        for sub in redditor.submissions.new(limit=20):
            if getattr(sub, "approved", False):
                return sub.title, True

        # If no approved posts, check comments
        for com in redditor.comments.new(limit=20):
            if getattr(com, "approved", False):
                snippet = com.body.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                return snippet, False
    except Exception as e:
        print(f"⚠️ Could not fetch last approved item for {username}: {e}")

    return None, None
