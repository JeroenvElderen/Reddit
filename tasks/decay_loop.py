def decay_loop():
    print("🕒 Decay loop started...")
    while True:
        try:
            now = datetime.now(current_tz())
            if now.hour == DECAY_RUN_HOUR:
                apply_decay_once()
                time.sleep(3600)
            else:
                time.sleep(300)
        except Exception as e:
            print(f"⚠️ Decay loop error: {e}")
            time.sleep(600)
