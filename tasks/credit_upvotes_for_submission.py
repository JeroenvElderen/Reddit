def credit_upvotes_for_submission(submission):
    """
    Convert net upvotes → karma for OP at a rate of 1 per 5 upvotes.
    Tracks credited_upvotes in Supabase to avoid double-paying.
    Also stores the post title for reference.
    """
    try:
        post_id = submission.id
        author = submission.author
        if author is None:
            return

        name = str(author)
        title_val = submission.title[:255] if hasattr(submission, "title") and submission.title else None

        # fetch tracking row
        res = supabase.table("post_upvote_credits").select("*").eq("post_id", post_id).execute()
        row = res.data[0] if res.data else None
        credited = int(row.get("credited_upvotes", 0)) if row else 0

        # current net score (floor at 0)
        try:
            score = int(getattr(submission, "score", 0) or 0)
        except Exception:
            score = 0
        score = max(0, score)

        delta_upvotes = score - credited
        if delta_upvotes <= 0:
            # nothing new → just refresh last_checked_at and store title
            supabase.table("post_upvote_credits").upsert({
                "post_id": post_id,
                "username": name,
                "credited_upvotes": credited,
                "last_checked_at": datetime.utcnow().isoformat(),
                "post_title": title_val,
            }).execute()
            return

        # 1 karma per 5 upvotes
        award = delta_upvotes // 5
        if award <= 0:
            # not enough to reach a new multiple of 5 yet → just refresh
            supabase.table("post_upvote_credits").upsert({
                "post_id": post_id,
                "username": name,
                "credited_upvotes": credited,
                "last_checked_at": datetime.utcnow().isoformat(),
                "post_title": title_val,
            }).execute()
            return

        # grant karma
        old_k, new_k, flair = apply_karma_and_flair(name, award, allow_negative=False)

        # save new credited count (consume award*5 upvotes)
        new_credited = credited + award * 5
        supabase.table("post_upvote_credits").upsert({
            "post_id": post_id,
            "username": name,
            "credited_upvotes": new_credited,
            "last_checked_at": datetime.utcnow().isoformat(),
            "post_title": title_val,
        }).execute()

        print(f"🏅 Upvote credit: u/{name} +{award} karma for {delta_upvotes} new upvotes (credited {new_credited})")

        # optional: log to Discord channel
        try:
            channel = bot.get_channel(DISCORD_UPVOTE_LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🏅 Upvote Reward",
                    description=f"u/{name} gained **+{award}** karma from post upvotes",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Post", value=f"https://reddit.com{submission.permalink}", inline=False)
                embed.add_field(name="Upvotes credited", value=f"{new_credited}", inline=True)
                embed.add_field(name="Karma", value=f"{old_k} → {new_k}", inline=True)
                embed.add_field(name="Flair", value=flair, inline=True)
                embed.add_field(name="Title", value=title_val or "—", inline=False)
                asyncio.run_coroutine_threadsafe(channel.send(embed=embed), bot.loop)
        except Exception as e:
            print(f"⚠️ Upvote reward log failed: {e}")

    except Exception as e:
        print(f"⚠️ credit_upvotes_for_submission failed: {e}")
