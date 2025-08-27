def _fetch_item_from_permalink(url: str):
    """
    Given a permalink like https://reddit.com/r/sub/comments/POSTID/title/COMMENTID/
    return the PRAW object (submission or comment).
    """
    try:
        p = urlparse(url)
        parts = [x for x in p.path.split("/") if x]
        # Expect: r/<sub>/comments/<post_id>/...[/<comment_id>/]
        if "comments" in parts:
            i = parts.index("comments")
            post_id = parts[i + 1]
            # If there's a trailing comment id, it will usually be at the end
            comment_id = parts[-1] if len(parts) > i + 3 else None
            # comment id must not equal post_id and usually is not "title" etc.
            if comment_id and comment_id != post_id and len(comment_id) in (7, 8):
                return reddit.comment(id=comment_id)
            return reddit.submission(id=post_id)
    except Exception:
        pass
    return None
