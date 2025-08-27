def reddit_polling():
    """Background polling for new subscribers + comments + posts."""
    print("🌍 Reddit polling started...")
    while True:
        try:
            
            # --- Existing logic: comments ---
            for comment in subreddit.comments(limit=10):
                handle_new_item(comment)

            # --- Existing logic: submissions ---
            for submission in subreddit.new(limit=5):
                handle_new_item(submission)

        except Exception as e:
            print(f"⚠️ Reddit poll error: {e}")
        time.sleep(15)
