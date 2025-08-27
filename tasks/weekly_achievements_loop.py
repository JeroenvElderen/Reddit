def weekly_achievements_loop():
    print("🕒 Weekly achievements loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            # Run every Sunday at 12:00
            if now.weekday() == 6 and now.hour == 12 and now.minute == 0:
                post_weekly_achievements()
                time.sleep(60)  # avoid duplicate run in same minute
        except Exception as e:
            print(f"⚠️ Weekly achievements loop error: {e}")
        time.sleep(30)
