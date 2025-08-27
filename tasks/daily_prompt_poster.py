def daily_prompt_poster():
    print("🕒 Daily prompt loop started...")
    while True:
        try:
            now = datetime.now(current_tz())

            # Runs once per day at 12:00
            if now.hour == 12 and now.minute == 0:
                today = now.date().isoformat()

                # Check if already posted today
                res = supabase.table("daily_bodypositive").select("*").eq("date_posted", today).execute()
                if res.data:
                    print("ℹ️ Body positivity already posted today, skipping.")
                    time.sleep(60)
                    continue

                # Always body positivity
                prompt = generate_body_positive()
                title = "💚 Body Positivity Prompt"

                # Submit post
                submission = subreddit.submit(title, selftext=prompt)

                # ✅ Auto-approve bot’s own daily posts
                try:
                    submission.mod.approve()
                    print("✅ Auto-approved Daily Prompt post")
                except Exception as e:
                    print(f"⚠️ Could not auto-approve Daily Prompt post: {e}")
                # Log bot's own post to Discord
                asyncio.run_coroutine_threadsafe(
                    send_discord_auto_log(
                        submission,
                        old_k=0, new_k=0,
                        flair="Daily Prompt",
                        awarded_points=0,
                        extras_note="Bot daily body positivity post"
                    ),
                    bot.loop
                
                )
                # Try to apply Daily Prompt flair
                daily_flair_id = flair_templates.get("Daily Prompt")
                if daily_flair_id:
                    try:
                        submission.flair.select(daily_flair_id)
                        print("🏷️ Flair set to Daily Prompt")
                    except Exception as e:
                        print(f"⚠️ Could not set flair: {e}")
                else:
                    print("ℹ️ No Daily Prompt flair ID configured, skipping flair")

                print(f"📢 Posted daily body positivity prompt")
                time.sleep(60)  # avoid double posting in same minute

        except Exception as e:
            print(f"⚠️ Daily prompt error: {e}")

        time.sleep(30)
