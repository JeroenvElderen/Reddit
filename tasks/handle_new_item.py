def handle_new_item(item):
    """Only process new, not-yet-moderated items; apply guardrails and route."""
    if item.author is None or item.id in seen_ids:
        return
    if already_moderated(item):
        print(f"⏩ Skipping {item.id} (already moderated)")
        seen_ids.add(item.id)
        return
    seen_ids.add(item.id)

    author_name = str(item.author)
    bot_username = os.getenv("REDDIT_USERNAME", "").lower()

    # 👇 NEW: ensure user exists in Supabase immediately
    try:
        res = supabase.table("user_karma").select("username").ilike("username", author_name).execute()
        is_new = not res.data

        supabase.table("user_karma").upsert({
            "username": author_name,
            "karma": 0,
            "last_flair": "Needs Growth"
        }).execute()

        if is_new:
            # Log to Discord channel 1410002767497527316
            channel = bot.get_channel(1410002767497527316)
            if channel:
                embed = discord.Embed(
                    title="👤 New User Detected",
                    description=f"u/{author_name} just made their first contribution!",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                awaitable = channel.send(embed=embed)
                try:
                    asyncio.run_coroutine_threadsafe(awaitable, bot.loop)
                except Exception:
                    pass

            print(f"🆕 New user logged: u/{author_name}")

    except Exception as e:
        print(f"⚠️ Failed to ensure user row for {author_name}: {e}")

    author_name = str(item.author)
    bot_username = os.getenv("REDDIT_USERNAME", "").lower()

    if author_name.lower() == bot_username:
        print(f"🤖 skipping queue for bot's own post/comment {item.id}")
        return

    res = supabase.table("user_karma").select("*").ilike("username", author_name).execute()
    karma = int(res.data[0]["karma"]) if res.data else 0

    # Language hinting
    text = item_text(item)
    if not likely_english(text):
        print("🈺 Language hint → manual")
        asyncio.run_coroutine_threadsafe(
            send_discord_approval(item, lang_label="Maybe non-English", note="Language hint"),
            bot.loop
        )
        return

    # Night Guard
    now_local = datetime.now(current_tz())
    if in_night_guard_window(now_local) and karma < NIGHT_GUARD_MIN_KARMA:
        print(f"🌙 Night Guard: u/{author_name} ({karma} < {NIGHT_GUARD_MIN_KARMA}) → manual")
        asyncio.run_coroutine_threadsafe(
            send_discord_approval(item, lang_label="English", note="Night Guard window", night_guard_ping=True),
            bot.loop
        )
        return

    # AUTO-APPROVE path (either high karma OR bot itself)
    bot_username = os.getenv("REDDIT_USERNAME", "").lower()
    
    # AUTO-APPROVE path (either high karma OR bot/owner)
    if karma >= 500 or author_name.lower() in (bot_username, OWNER_USERNAME):
        item.mod.approve()
        old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=False)

        # Prevent karma/flair only for the bot itself
        if author_name.lower() == bot_username:
            old_k, new_k, flair, total_delta, extras = 0, 0, "—", 0, ""
    
        note = f"+{total_delta}" + (f" ({extras})" if extras else "")
        print(f"✅ Auto-approved u/{author_name} ({old_k}→{new_k}) {note}")

        # also log to approval log channel
        asyncio.run_coroutine_threadsafe(
            log_approval(item, old_k, new_k, flair, note),
            bot.loop
        )
        return

    # Otherwise: manual review
    print(f"📨 Queueing u/{author_name} ({karma} karma) → manual")
    asyncio.run_coroutine_threadsafe(
        send_discord_approval(item, lang_label="English"),
        bot.loop
    )
