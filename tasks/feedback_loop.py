def feedback_loop():
    print("🕒 Feedback loop started...")
    while True:
        try:
            today = datetime.now(current_tz()).date()
            rows = supabase.table("user_karma").select("*").execute().data or []

            for row in rows:
                name = row.get("username")
                if not name:
                    continue

                last_approved = row.get("last_approved_date")
                if not last_approved:
                    continue

                try:
                    joined = date.fromisoformat(last_approved)
                except Exception:
                    continue

                days_active = (today - joined).days

                # 1 Month Feedback
                if days_active >= 30 and not row.get("feedback_1m_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1m_feedback"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1m_sent": True}
                    ).ilike("username", name).execute()

                # 1 Week Rule Opinion
                if days_active >= 7 and not row.get("feedback_1w_rule_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1w_rules"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1w_rule_sent": True}
                    ).ilike("username", name).execute()

                # 1 Week Prompt Opinion
                if days_active >= 7 and not row.get("feedback_1w_prompt_sent"):
                    asyncio.run_coroutine_threadsafe(
                        send_owner_feedback(name, "1w_prompts"), bot.loop
                    )
                    supabase.table("user_karma").update(
                        {"feedback_1w_prompt_sent": True}
                    ).ilike("username", name).execute()

        except Exception as e:
            print(f"⚠️ Feedback loop error: {e}")

        time.sleep(86400)
