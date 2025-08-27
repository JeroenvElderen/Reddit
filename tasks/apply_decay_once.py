def apply_decay_once():
    if not DECAY_ENABLED:
        return
    try:
        rows = supabase.table("user_karma").select("*").execute().data or []
    except Exception as e:
        print(f"⚠️ Decay query failed: {e}")
        return

    today_local = datetime.now(current_tz()).date()

    for row in rows:
        name = row.get("username")
        karma = int(row.get("karma", 0))
            # 🌙 Observer: track days spent in Observer
        if row.get("last_flair") == "Quiet Observer":
            days = int(row.get("observer_days", 0)) + 1
            supabase.table("user_karma").upsert({
                "username": name,
                "observer_days": days
            }).execute()
            row["observer_days"] = days
            check_observer_badges(name, row)

        if karma <= 0:
            continue

        last_approved = row.get("last_approved_date")
        last_decay = row.get("last_decay_date")
        try:
            la = date.fromisoformat(last_approved) if last_approved else None
        except Exception:
            la = None
        try:
            ld = date.fromisoformat(last_decay) if last_decay else None
        except Exception:
            ld = None

        since = (today_local - (la or today_local)).days
        if since == (DECAY_AFTER_DAYS - 1):
            flair = get_flair_for_karma(karma)
            asyncio.run_coroutine_threadsafe(
                send_decay_warning(name, since, karma, flair),
                bot.loop
            )
        
        if since <= DECAY_AFTER_DAYS:
            continue

        start_point = (la or today_local) + timedelta(days=DECAY_AFTER_DAYS)
        if ld:
            start_point = max(start_point, ld)

        days_to_decay = (today_local - start_point).days
        if days_to_decay <= 0:
            continue

        delta = -DECAY_PER_DAY * days_to_decay
        old_k, new_k, flair = apply_karma_and_flair(name, delta, allow_negative=False)
        try:
            supabase.table("user_karma").upsert({
                "username": name,
                "last_decay_date": today_local.isoformat(),
            }).execute()
        except Exception:
            pass
        print(f"🍂 Decay: u/{name} {old_k}→{new_k} (-{abs(delta)})")
