def upvote_reward_loop():
    print("🕒 Upvote reward loop started...")
    while True:
        try:
            # Pull a reasonable window of fresh posts; adjust as needed
            for sub in subreddit.new(limit=100):
                try:
                    # only process approved posts (avoid queueing/removals)
                    if not getattr(sub, "approved", False):
                        continue
                    # credit upvotes to OP
                    credit_upvotes_for_submission(sub)
                except Exception as e:
                    print(f"⚠️ Upvote credit per-post error: {e}")

        except Exception as e:
            print(f"⚠️ Upvote reward loop error: {e}")

        # Sleep a bit; tune for your load
        time.sleep(120)
