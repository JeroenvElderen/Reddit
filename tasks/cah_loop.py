def cah_loop():
    print("🕒 CAH loop started...")
    while True:
        try:
            if not CAH_ENABLED:
                time.sleep(60)
                continue

            now = datetime.now(current_tz())

            # ---------- 1) Post a NEW ROUND at the scheduled hour ----------
            if now.hour == CAH_POST_HOUR and now.minute == 0:
                # Do NOT post if an existing round is still active
                try:
                    open_rows = (
                        supabase.table("cah_rounds")
                        .select("round_id,status,post_id,lock_after_ts")
                        .in_("status", ["open", "extended"])
                        .limit(1)
                        .execute()
                        .data
                        or []
                    )
                except Exception as e:
                    open_rows = []
                    print(f"⚠️ Could not check active rounds: {e}")

                if open_rows:
                    # A round is still active → skip posting a new one
                    try:
                        asyncio.run_coroutine_threadsafe(
                            log_cah_event(
                                "⛔ Skipped New Round",
                                "A CAH round is still active (open/extended). No new round posted.",
                            ),
                            bot.loop,
                        )
                    except Exception:
                        pass
                    time.sleep(60)  # avoid repost in same minute
                    continue

                # Verify we have enabled packs & cards
                active = cah_enabled_packs()
                if not active:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            log_cah_event("⚠️ Skipped New Round", "No enabled packs."),
                            bot.loop,
                        )
                    except Exception:
                        pass
                    time.sleep(60)
                    continue

                total_cards = 0
                for p in active:
                    try:
                        cnt = (
                            supabase.table("cah_black_cards")
                            .select("id", count="exact")
                            .eq("pack_key", p["key"])
                            .execute()
                        )
                        total_cards += cnt.count or 0
                    except Exception:
                        pass
                if total_cards <= 0:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            log_cah_event("⚠️ Skipped New Round", "No cards available in enabled packs."),
                            bot.loop,
                        )
                    except Exception:
                        pass
                    time.sleep(60)
                    continue

                # Pick card & build post body (with previous winner block)
                black = cah_pick_black_card()
                header = _fetch_last_winner_block()  # may return ""
                leaf_sep = "🌿" * 17  # 17 leaves in a row

                body = (
                    "🌿🌞🌿🌞🌿🌞🌿🌞🌿\n\n"
                    "# 🎲 Cards Against Humanity: Naturist Edition 🎲\n\n"
                    f"{header}"
                    f"{leaf_sep}\n\n"
                    "✨ **Black Card of the Day:**\n"
                    f"> {black}\n\n"
                    f"{leaf_sep}\n\n"
                    "📝 **How to Play:**\n"
                    "1. Comment your funniest answer below (fill in the blank).\n"
                    "2. Upvote your favorites.\n"
                    "3. The top reply after 24h wins 🏆.\n\n"
                    "🌿🌞🌿🌞🌿🌞🌿🌞🌿"
                )


                # Post to Reddit
                title = "🎲 CAH Round — Fill in the Blank!"
                submission = reddit_owner.subreddit(SUBREDDIT_NAME).submit(title, selftext=body)

                if CAH_POST_FLAIR_ID:
                    try:
                        submission.flair.select(CAH_POST_FLAIR_ID)
                    except Exception:
                        pass

                try:
                    submission.mod.approve()
                    print("✅ Auto-approved CAH post")
                except Exception as e:
                    print(f"⚠️ Could not auto-approve CAH post: {e}")

                # Record the round
                round_id = str(uuid.uuid4())
                start_ts = datetime.utcnow()
                lock_after = start_ts + timedelta(hours=CAH_ROUND_DURATION_H)
                try:
                    supabase.table("cah_rounds").insert(
                        {
                            "round_id": round_id,
                            "post_id": submission.id,
                            "black_text": black,
                            "start_ts": start_ts.isoformat(),
                            "status": "open",
                            "lock_after_ts": lock_after.isoformat(),
                        }
                    ).execute()
                except Exception as e:
                    print(f"⚠️ Could not insert new cah_round: {e}")

                # Log to Discord
                try:
                    asyncio.run_coroutine_threadsafe(
                        log_cah_event(
                            "🎲 New Round Posted",
                            f"Black card: **{black}**\n[Reddit link](https://reddit.com{submission.permalink})",
                        ),
                        bot.loop,
                    )
                except Exception:
                    pass

                time.sleep(60)  # avoid duplicate post in same minute

            # ---------- 2) CLOSE/EXTEND open rounds at lock time (24h) ----------
            rows = (
                supabase.table("cah_rounds")
                .select("*")
                .eq("status", "open")
                .execute()
                .data
                or []
            )

            for r in rows:
                try:
                    post = reddit.submission(id=r["post_id"])
                except Exception:
                    continue

                # lock_after_ts might be ISO (with or without Z)
                latxt = r.get("lock_after_ts", "")
                try:
                    lock_after_dt = (
                        datetime.fromisoformat(latxt.replace("Z", "+00:00"))
                        if "Z" in latxt
                        else datetime.fromisoformat(latxt)
                    )
                except Exception:
                    lock_after_dt = datetime.utcnow()

                if datetime.utcnow() >= lock_after_dt:
                    # 24h reached – decide if we close or extend
                    try:
                        post.comments.replace_more(limit=0)
                        comments = list(post.comments)
                    except Exception:
                        comments = []

                    # First lock point: if it's the first time we hit 24h
                    if r.get("comments_at_24h") is None:
                        if comments:
                            # Close & pick winner
                            winner = None
                            top = -1
                            for c in comments:
                                try:
                                    sc = int(getattr(c, "score", 0) or 0)
                                except Exception:
                                    sc = 0
                                if sc > top:
                                    top = sc
                                    winner = (c.author.name if c.author else None, c.id, sc)

                            try:
                                post.mod.lock()
                            except Exception:
                                pass

                            supabase.table("cah_rounds").update(
                                {
                                    "status": "closed",
                                    "comments_at_24h": len(comments),
                                    "winner_username": winner[0] if winner else None,
                                    "winner_comment_id": winner[1] if winner else None,
                                    "winner_score": winner[2] if winner else None,
                                }
                            ).eq("round_id", r["round_id"]).execute()

                            try:
                                asyncio.run_coroutine_threadsafe(
                                    log_cah_event(
                                        "🏆 Round Closed",
                                        (
                                            f"Winner: u/{winner[0]} (+{winner[2]})"
                                            if winner and winner[0]
                                            else "No winner"
                                        ),
                                    ),
                                    bot.loop,
                                )
                            except Exception:
                                pass
                        else:
                            # No comments – extend for CAH_EXTENSION_H
                            new_lock = datetime.utcnow() + timedelta(hours=CAH_EXTENSION_H)
                            supabase.table("cah_rounds").update(
                                {
                                    "status": "extended",
                                    "comments_at_24h": 0,
                                    "lock_after_ts": new_lock.isoformat(),
                                }
                            ).eq("round_id", r["round_id"]).execute()

                            try:
                                asyncio.run_coroutine_threadsafe(
                                    log_cah_event(
                                        "⏳ Round Extended",
                                        "No comments after 24h, extended for another period.",
                                    ),
                                    bot.loop,
                                )
                            except Exception:
                                pass

            # ---------- 3) CLOSE extended rounds at second lock ----------
            rows_ext = (
                supabase.table("cah_rounds")
                .select("*")
                .eq("status", "extended")
                .execute()
                .data
                or []
            )

            for r in rows_ext:
                try:
                    post = reddit.submission(id=r["post_id"])
                except Exception:
                    continue

                # lock_after_ts might be ISO (with or without Z)
                latxt = r.get("lock_after_ts", "")
                try:
                    lock_after_dt = (
                        datetime.fromisoformat(latxt.replace("Z", "+00:00"))
                        if "Z" in latxt
                        else datetime.fromisoformat(latxt)
                    )
                except Exception:
                    lock_after_dt = datetime.utcnow()

                if datetime.utcnow() >= lock_after_dt:
                    # Final close regardless of comments
                    try:
                        post.comments.replace_more(limit=0)
                        comments = list(post.comments)
                    except Exception:
                        comments = []

                    winner = None
                    top = -1
                    for c in comments:
                        try:
                            sc = int(getattr(c, "score", 0) or 0)
                        except Exception:
                            sc = 0
                        if sc > top:
                            top = sc
                            winner = (c.author.name if c.author else None, c.id, sc)

                    try:
                        post.mod.lock()
                    except Exception:
                        pass

                    supabase.table("cah_rounds").update(
                        {
                            "status": "closed",
                            "winner_username": winner[0] if winner else None,
                            "winner_comment_id": winner[1] if winner else None,
                            "winner_score": winner[2] if winner else None,
                        }
                    ).eq("round_id", r["round_id"]).execute()

                    try:
                        asyncio.run_coroutine_threadsafe(
                            log_cah_event(
                                "🏆 Round Closed (after extension)",
                                (
                                    f"Winner: u/{winner[0]} (+{winner[2]})"
                                    if winner and winner[0]
                                    else "No winner"
                                ),
                            ),
                            bot.loop,
                        )
                    except Exception:
                        pass

            time.sleep(30)

        except Exception as e:
            print(f"⚠️ CAH loop error: {e}")
            time.sleep(60)
