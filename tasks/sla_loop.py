def sla_loop():
    print("⏱️ SLA monitor started...")
    while True:
        try:
            now = time.time()
            for msg_id in list(pending_reviews.keys()):
                entry = pending_reviews.get(msg_id)
                if not entry:
                    continue
                last = entry.get("last_escalated_ts", entry.get("created_ts", now))
                if now - last >= SLA_MINUTES * 60:
                    entry["last_escalated_ts"] = now
                    asyncio.run_coroutine_threadsafe(_escalate_card(msg_id), bot.loop)
                    pending_reviews.pop(msg_id, None)
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ SLA loop error: {e}")
            time.sleep(30)
