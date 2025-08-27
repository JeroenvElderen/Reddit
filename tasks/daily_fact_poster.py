def daily_fact_poster():
    print("🕒 Daily fact loop started...")
    while True:
        try:
            now = datetime.now(current_tz())

            # Runs once per day at 08:00 (midnight)
            if now.hour == 8 and now.minute == 0:
                today = now.date().isoformat()

                # Skip if already posted today
                res = supabase.table("daily_facts").select("*").eq("date_posted", today).execute()
                if res.data:
                    print("ℹ️ Fact already posted today, skipping.")
                    time.sleep(60)
                    continue

                fact = generate_naturist_fact()
                title = "🌿 Naturist Fact of the Day"

                # Submit post
                submission = subreddit.submit(title, selftext=fact)

                # ✅ Auto-approve bot’s own daily posts
                try:
                    submission.mod.approve()
                    print("✅ Auto-approved Naturist Fact post")
                except Exception as e:
                    print(f"⚠️ Could not auto-approve Naturist Fact post: {e}")
                
                # Log bot's own post to Discord
                asyncio.run_coroutine_threadsafe(
                    send_discord_auto_log(
                        submission,
                        old_k=0, new_k=0,
                        flair="Daily Prompt",
                        awarded_points=0,
                        extras_note="Bot daily fact post"
                    ),
                    bot.loop
                )
                
                # Apply Daily Prompt flair (reuse same one if you want)
                daily_flair_id = flair_templates.get("Daily Prompt")
                if daily_flair_id:
                    try:
                        submission.flair.select(daily_flair_id)
                        print("🏷️ Flair set to Daily Prompt")
                    except Exception as e:
                        print(f"⚠️ Could not set flair: {e}")

                print(f"📢 Posted daily fact: {title}")
                time.sleep(60)

        except Exception as e:
            print(f"⚠️ Daily fact error: {e}")

        time.sleep(30)
