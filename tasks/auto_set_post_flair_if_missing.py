def auto_set_post_flair_if_missing(submission):
    if not hasattr(submission, "title"):
        return
    if getattr(submission, "link_flair_text", None) or getattr(submission, "link_flair_template_id", None):
        return
    try:
        title = (submission.title or "").lower()
        body = (submission.selftext or "").lower()
        for kw, tmpl in KEYWORD_MAP.items():
            if kw in title or kw in body:
                if tmpl:
                    submission.flair.select(tmpl)
                    print(f"🏷️ Post flair (keyword '{kw}') set via template {tmpl}")
                    return
        if (POST_FLAIR_IMAGE_ID and (is_native_reddit_image(submission) or submission_has_any_image(submission))):
            submission.flair.select(POST_FLAIR_IMAGE_ID); print(f"🏷️ Post flair (image) set via template {POST_FLAIR_IMAGE_ID}")
        elif POST_FLAIR_TEXT_ID and body.strip():
            submission.flair.select(POST_FLAIR_TEXT_ID);  print(f"🏷️ Post flair (text) set via template {POST_FLAIR_TEXT_ID}")
        elif POST_FLAIR_LINK_ID:
            submission.flair.select(POST_FLAIR_LINK_ID);  print(f"🏷️ Post flair (link) set via template {POST_FLAIR_LINK_ID}")
    except Exception as e:
        print(f"⚠️ Post flair set failed: {e}")
