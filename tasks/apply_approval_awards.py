def apply_approval_awards(item, is_manual: bool):
    author = item.author
    name = str(author)
    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
    row = res.data[0] if res.data else {}
    old_k = int(row.get("karma", 0))
    last_date_s = row.get("last_approved_date")
    streak_days = int(row.get("streak_days", 0))
    welcomed = bool(row.get("welcomed", False))

    # base
    if hasattr(item, "title"):
        base = 5 if is_native_reddit_image(item) else 1
    else:
        base = 1

    extras = []

    # streak update (by local date)
    today = datetime.now(current_tz()).date()
    yesterday = today - timedelta(days=1)
    last_date = None
    if last_date_s:
        try:
            last_date = date.fromisoformat(last_date_s)
        except Exception:
            last_date = None

    if last_date == today:
        pass
    elif last_date == yesterday:
        streak_days += 1
    else:
        streak_days = 1

    streak_bonus = 0
    if STREAK_ENABLED and streak_days >= STREAK_MIN_DAYS:
        streak_bonus = min(STREAK_DAILY_BONUS, STREAK_MAX_BONUS_PER_DAY)
        if streak_bonus > 0:
            extras.append(f"streak +{streak_bonus} (streak {streak_days}d)")

    # quality vote (posts only)
    qv_bonus = 0
    if hasattr(item, "title"):
        qv_bonus = calc_quality_bonus_for_post(item)
        if qv_bonus > 0:
            extras.append(f"quality +{qv_bonus} (score {getattr(item,'score',0)})")

    total_delta = base + streak_bonus + qv_bonus
    old_k2, new_k, flair = apply_approval_points_and_flair(item, total_delta)

    # write back streak + last approved date + welcomed
    try:
        supabase.table("user_karma").upsert({
            "username": name,
            "streak_days": streak_days,
            "last_approved_date": today.isoformat(),
            "welcomed": welcomed or (old_k == 0),
        }).execute()
    except Exception:
        pass

    try:
        if old_k == 0:
            on_first_approval_welcome(item, name, old_k)
    except Exception:
        pass

    # optional auto-tagger (off unless envs set)
    try:
        if hasattr(item, "title"):
            auto_set_post_flair_if_missing(item)
    except Exception:
        pass

    try:
        if hasattr(item, "title"):  # only posts, not comments
            increment_location_counter(item, name)

            # Increment Pillars (simple keyword-based example)
            title_body = (getattr(item, "title", "") + " " + getattr(item, "selftext", "")).lower()
            pillar_fields = {
                "body": "bodypositivity_posts_count",
                "travel": "travel_posts_count",
                "mind": "mindfulness_posts_count",
                "advocacy": "advocacy_posts_count",
            }
            for kw, field in pillar_fields.items():
                if kw in title_body:
                    res = supabase.table("user_karma").select("*").ilike("username", name).execute()
                    row = res.data[0] if res.data else {}
                    current = int(row.get(field, 0))
                    new_val = current + 1
                    supabase.table("user_karma").upsert({"username": name, field: new_val}).execute()
                    check_pillar_badge(name, field, new_val)

            # Meta ladder → total naturist posts
            res = supabase.table("user_karma").select("*").ilike("username", name).execute()
            row = res.data[0] if res.data else {}
            total = int(row.get("naturist_total_posts", 0)) + 1
            supabase.table("user_karma").upsert({"username": name, "naturist_total_posts": total}).execute()
            check_meta_badge(name, total)

            # Seasonal (detect by post flair or month)
            month = datetime.utcnow().month
            field_map = {12: "posted_in_winter", 1: "posted_in_winter", 2: "posted_in_winter",
                         3: "posted_in_spring", 4: "posted_in_spring", 5: "posted_in_spring",
                         6: "posted_in_summer", 7: "posted_in_summer", 8: "posted_in_summer",
                         9: "posted_in_autumn", 10: "posted_in_autumn", 11: "posted_in_autumn"}
            season_field = field_map.get(month)
            if season_field:
                supabase.table("user_karma").update({season_field: True}).ilike("username", name).execute()

            # Check Seasonal & Rare
            row = supabase.table("user_karma").select("*").ilike("username", name).execute().data[0]
            check_seasonal_and_rare(name, row)

        # 🌙 Observer contribution + support
        if row.get("last_flair") == "Quiet Observer":
            if not hasattr(item, "title"):  # comment
                comments = int(row.get("observer_comments_count", 0)) + 1
                supabase.table("user_karma").upsert({
                    "username": name,
                    "observer_comments_count": comments
                }).execute()
                row["observer_comments_count"] = comments

            # add upvotes (both posts & comments)
            try:
                score = int(getattr(item, "score", 0) or 0)
            except Exception:
                score = 0
            upvotes = int(row.get("observer_upvotes_total", 0)) + score
            supabase.table("user_karma").upsert({
                "username": name,
                "observer_upvotes_total": upvotes
            }).execute()
            row["observer_upvotes_total"] = upvotes

            check_observer_badges(name, row)

    except Exception as e:
        print(f"⚠️ Achievement ladder failed: {e}")


    return old_k2, new_k, flair, total_delta, ("; ".join(extras) if extras else "")
