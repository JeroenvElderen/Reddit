def backfill_location_counts(username: str):
    """Rescan approved submissions for a user, update counts, and award badges."""
    redditor = reddit.redditor(username)

    # location counts
    loc_counts = {v: 0 for v in FLAIR_TO_FIELD.values()}

    # pillars (same simple keyword logic you use on approval)
    pillar_fields = {
        "body": "bodypositivity_posts_count",
        "travel": "travel_posts_count",
        "mind": "mindfulness_posts_count",
        "advocacy": "advocacy_posts_count",
    }
    pillar_counts = {v: 0 for v in pillar_fields.values()}

    total_posts = 0

    try:
        for sub in redditor.submissions.new(limit=500):
            if str(sub.subreddit).lower() != SUBREDDIT_NAME.lower():
                continue
            if not getattr(sub, "approved", False):
                continue

            total_posts += 1

            # --- location flair tally
            flair_text = _text_flair_without_emoji(sub)
            key = _normalize_flair_key(flair_text)
            field = FLAIR_TO_FIELD_NORM.get(key)
            if field:
                loc_counts[field] += 1

            # --- pillars (keyword-based)
            tb = ((getattr(sub, "title", "") or "") + " " + (getattr(sub, "selftext", "") or "")).lower()
            for kw, fld in pillar_fields.items():
                if kw in tb:
                    pillar_counts[fld] += 1

        # upsert totals to Supabase
        payload = {"username": username, **loc_counts, **pillar_counts, "naturist_total_posts": total_posts}
        supabase.table("user_karma").upsert(payload).execute()
        print(f"✅ Recounted for u/{username}: locations={loc_counts}, pillars={pillar_counts}, total={total_posts}")

        # award/refresh badges (these functions delete older levels, insert latest, and log to Discord)
        for field, c in loc_counts.items():
            if c > 0:
                check_and_award_badge(username, field, c)
        for field, c in pillar_counts.items():
            if c > 0:
                check_pillar_badge(username, field, c)
        check_meta_badge(username, total_posts)

        return {"locations": loc_counts, "pillars": pillar_counts, "total": total_posts}

    except Exception as e:
        print(f"⚠️ Recount failed for {username}: {e}")
        return None
