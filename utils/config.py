openai.api_key = os.getenv("OPENAI_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

reddit_owner = praw.Reddit(
    client_id=os.getenv("OWNER_REDDIT_CLIENT_ID"),
    client_secret=os.getenv("OWNER_REDDIT_CLIENT_SECRET"),
    username=os.getenv("OWNER_REDDIT_USERNAME"),
    password=os.getenv("OWNER_REDDIT_PASSWORD"),
    user_agent=os.getenv("OWNER_REDDIT_USER_AGENT"),
)

SUBREDDIT_NAME = "PlanetNaturists"

subreddit = reddit.subreddit(SUBREDDIT_NAME)

BOT_USERNAME = os.getenv("REDDIT_USERNAME", "").lower()

BOT_FLAIR_ID = os.getenv("BOT_FLAIR_ID", "ce269096-81b1-11f0-b51d-6ecc7a96815b")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

DISCORD_DECAY_LOG_CHANNEL_ID = int(os.getenv("DISCORD_DECAY_LOG_CHANNEL_ID", "1408406356582731776"))

DISCORD_APPROVAL_LOG_CHANNEL_ID = int(os.getenv("DISCORD_APPROVAL_LOG_CHANNEL_ID", "1408406760322240572"))

DISCORD_REJECTION_LOG_CHANNEL_ID = int(os.getenv("DISCORD_REJECTION_LOG_CHANNEL_ID", "1408406824453148725"))

DISCORD_ACHIEVEMENTS_CHANNEL_ID = int(os.getenv("DISCORD_ACHIEVEMENTS_CHANNEL_ID", "1409902857947185202"))

DISCORD_UPVOTE_LOG_CHANNEL_ID = int(os.getenv("DISCORD_UPVOTE_LOG_CHANNEL_ID", "1409916507609235556"))

DISCORD_AUTO_APPROVAL_CHANNEL_ID = int(os.getenv("DISCORD_AUTO_APPROVAL_CHANNEL_ID", "1408406760322240572"))

DISCORD_CAH_CHANNEL_ID = int(os.getenv("DISCORD_CAH_CHANNEL_ID", "1410224656526610432"))

intents = discord.Intents.default()

intents.messages = True

intents.reactions = True

intents.guilds = True

intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CAH_PAGE_SIZE = int(os.getenv("CAH_PAGE_SIZE","20"))

CAH_ENABLED = os.getenv("CAH_ENABLED","0") == "1"

CAH_POST_HOUR = int(os.getenv("CAH_POST_HOUR","12"))

CAH_ROUND_DURATION_H = int(os.getenv("CAH_ROUND_DURATION_H","24"))

CAH_EXTENSION_H = int(os.getenv("CAH_EXTENSION_H","24"))

CAH_INCLUDE_BASE = os.getenv("CAH_INCLUDE_BASE","1") == "1"

CAH_BASE_PACK_KEY = os.getenv("CAH_BASE_PACK_KEY","base")

CAH_POST_FLAIR_ID = os.getenv("CAH_POST_FLAIR_ID") or None

DISCORD_CAH_CHANNEL_ID = int(os.getenv("DISCORD_CAH_CHANNEL_ID","0"))

TZ_NAME = os.getenv("TZ", "Europe/Dublin")

NIGHT_GUARD_ENABLED = os.getenv("NIGHT_GUARD_ENABLED", "1") == "1"

NIGHT_GUARD_WINDOW = os.getenv("NIGHT_GUARD_WINDOW", "00:00-06:00")

NIGHT_GUARD_MIN_KARMA = int(os.getenv("NIGHT_GUARD_MIN_KARMA", "1000"))

MOD_PING_ROLE_ID = int(os.getenv("MOD_PING_ROLE_ID", "0"))

MOD_PING_COOLDOWN_SEC = int(os.getenv("MOD_PING_COOLDOWN_SEC", "600"))

_last_mod_ping_ts = 0.0

DECAY_ENABLED = os.getenv("DECAY_ENABLED", "1") == "1"

DECAY_AFTER_DAYS = int(os.getenv("DECAY_AFTER_DAYS", "7"))

DECAY_PER_DAY = int(os.getenv("DECAY_PER_DAY", "1"))

DECAY_RUN_HOUR = int(os.getenv("DECAY_RUN_HOUR", "3"))

STREAK_ENABLED = os.getenv("STREAK_ENABLED", "1") == "1"

STREAK_MIN_DAYS = int(os.getenv("STREAK_MIN_DAYS", "3"))

STREAK_DAILY_BONUS = int(os.getenv("STREAK_DAILY_BONUS", "1"))

STREAK_MAX_BONUS_PER_DAY = int(os.getenv("STREAK_MAX_BONUS_PER_DAY", "1"))

QV_ENABLED = os.getenv("QV_ENABLED", "1") == "1"

QV_STEP_SCORE = int(os.getenv("QV_STEP_SCORE", "25"))

QV_BONUS_PER_STEP = int(os.getenv("QV_BONUS_PER_STEP", "1"))

QV_MAX_BONUS = int(os.getenv("QV_MAX_BONUS", "5"))

WELCOME_ENABLED = os.getenv("WELCOME_ENABLED", "1") == "1"

SLA_MINUTES = int(os.getenv("SLA_MINUTES", "5"))

SLA_PRIORITY_PREFIX = os.getenv("SLA_PRIORITY_PREFIX", "🔥 PRIORITY")

ETA_SAMPLE_WINDOW_MIN = int(os.getenv("ETA_SAMPLE_WINDOW_MIN", "60"))

ETA_ACTIVE_REVIEWER_TIMEOUT_MIN = int(os.getenv("ETA_ACTIVE_REVIEWER_TIMEOUT_MIN", "10"))

ETA_MIN_SEC = int(os.getenv("ETA_MIN_SEC", "60"))

ETA_MAX_SEC = int(os.getenv("ETA_MAX_SEC", "3600"))

ETA_DEFAULT_DECISION_SEC = int(os.getenv("ETA_DEFAULT_DECISION_SEC", "180"))

POST_FLAIR_IMAGE_ID = os.getenv("POST_FLAIR_IMAGE_ID", "")

POST_FLAIR_TEXT_ID = os.getenv("POST_FLAIR_TEXT_ID", "")

POST_FLAIR_LINK_ID = os.getenv("POST_FLAIR_LINK_ID", "")

POST_FLAIR_KEYWORDS = os.getenv("POST_FLAIR_KEYWORDS", "")

OWNER_USERNAME = os.getenv("OWNER_REDDIT_USERNAME", "").lower()

PACK_SCHEDULE = {
    "spring": {"start": (3, 1), "end": (5, 31)},    # Mar 1 – May 31
    "summer": {"start": (6, 1), "end": (8, 31)},    # Jun 1 – Aug 31
    "autumn": {"start": (9, 1), "end": (11, 30)},   # Sep 1 – Nov 30
    "winter": {"start": (12, 1), "end": (2, 28)},   # Dec 1 – Feb 28 (ignore leap day for simplicity)
    "halloween": {"start": (10, 25), "end": (11, 1)},   # late Oct → Nov 1
    "christmas": {"start": (12, 20), "end": (12, 27)},
    "newyear": {"start": (12, 30), "end": (1, 2)},
    "easter": {"start": (3, 25), "end": (4, 5)},     # varies yearly, pick approx
    "midsummer": {"start": (6, 20), "end": (6, 25)},
    "pride": {"start": (6, 1), "end": (6, 30)},
    "stpatricks": {"start": (3, 15), "end": (3, 18)},
    "valentines": {"start": (2, 13), "end": (2, 15)},
    "earthday": {"start": (4, 22), "end": (4, 23)},
}

REJECTION_REASONS = {
    "1️⃣": "Rule 1: This is a naturist space, not a fetish subreddit.",
    "2️⃣": "Rule 2: Respect consent and privacy.",
    "3️⃣": "Rule 3: Nudity allowed, never sexualized.",
    "4️⃣": "Rule 4: No content involving minors.",
    "5️⃣": "Rule 5: Be kind, civil, and body-positive.",
    "6️⃣": "Rule 6: Keep it on-topic.",
    "7️⃣": "Rule 7: Tag nudity as NSFW.",
    "8️⃣": "Rule 8: No creepy or inappropriate behavior.",
    "9️⃣": "Rule 9: No advertising or promotion.",
    "🔟": "Rule 10: Be mindful when sharing personal photos.",
    "📝": "Removed because it had no meaningful addition to the post or discussion.",
    "✏️": "Custom reason (to be filled manually)",

}

NATURIST_EMOJIS = [
    "🌿", "🌞", "🌊", "✨", "🍂", "❄️", "🌸", "☀️",
    "👣", "🌍", "💚", "🌴", "🏕️", "🧘", "🌳", "🏖️", "🔥"
]

flair_ladder = [
    ("Cover Curious", 0),
    ("First Bare", 10),
    ("Skin Fresh", 50),
    ("Sun Chaser", 100),
    ("Breeze Walker", 250),
    ("Clothing Free", 500),
    ("Open Air", 1000),
    ("True Naturist", 2000),
    ("Bare Master", 5000),
    ("Naturist Legend", 10000),
]

flair_templates = {
    "Needs Growth": "75c23a86-7f6d-11f0-8745-f666d1d62ce4",
    "Cover Curious": "ae791af4-7d22-11f0-934a-2e3446070201",
    "First Bare": "bbf4d5d8-7d22-11f0-b485-d64b23d9d74f",
    "Skin Fresh": "c5be4a5e-7d22-11f0-b278-0298fe10eba2",
    "Sun Chaser": "d72ca790-7d22-11f0-a0de-a687510f7c1a",
    "Breeze Walker": "e35fc826-7d22-11f0-8742-d64b23d9d74f",
    "Clothing Free": "f01b2e02-7d22-11f0-bee0-7e43d54e1cf4",
    "Open Air": "7cfdbc2c-7dd7-11f0-9936-9e1c00b89022",
    "True Naturist": "8a5fbeb0-7dd7-11f0-9fa7-2e98a4cf4302",
    "Bare Master": "987da246-7dd7-11f0-ae7f-8206f7eb2e0a",
    "Naturist Legend": "a3f1f8fc-7dd7-11f0-b2c1-227301a06778",
    "Daily Prompt": "8b04873e-80d8-11f0-81d2-260f76f8fd83",
    "Quiet Observer": "a3d0f81c-81c6-11f0-a40f-028908714e28",
}

FLAIR_TO_FIELD = {
    "Beach": "beach_posts_count",
    "Lake": "lake_posts_count",
    "River": "river_posts_count",
    "Hot Spring": "hotspring_posts_count",
    "Poolside": "pool_posts_count",
    "Forest": "forest_posts_count",
    "Mountain": "mountain_posts_count",
    "Meadow": "meadow_posts_count",
    "Desert": "desert_posts_count",
    "Cave": "cave_posts_count",
    "Tropical": "tropical_posts_count",
    "Nordic / Cold": "nordic_posts_count",
    "Island": "island_posts_count",
    "Urban": "urban_posts_count",
    "Countryside": "countryside_posts_count",
    "Festival": "festival_posts_count",
    "Resort / Club": "resort_posts_count",
    "Camping": "camping_posts_count",
    "Backyard / Home": "backyard_posts_count",
    "Sauna / Spa": "sauna_posts_count",
}

FLAIR_TO_FIELD_NORM = { _normalize_flair_key(k): v for k, v in FLAIR_TO_FIELD.items() }

BADGE_THRESHOLDS = [3, 7, 15, 30, 50]

PILLAR_THRESHOLDS = [1, 3, 5, 10, 15, 25, 40, 60, 80, 100]

META_THRESHOLDS = [10, 25, 50, 100, 150, 200, 300, 400, 500, 1000]

META_TITLES = [
    "Curious Explorer 🌱",
    "Bare Adventurer 👣",
    "Naturist Voice 🗣️",
    "Nature Friend 🌿",
    "Community Root 🌳",
    "Sun Chaser 🌞",
    "Open Spirit ✨",
    "Earth Child 🌍",
    "Naturist Sage 🧘",
    "Naturist Legend 👑"
]

pending_reviews = {}

seen_ids = set()

decision_durations = []

mod_activity = {}

try:
    from zoneinfo import ZoneInfo
except Exception:
    from backports.zoneinfo import ZoneInfo

async def send_decay_warning(username: str, days_since: int, karma: int, flair: str):
    """Send a friendly personalized decay reminder from OWNER account."""
    try:
        last_text, is_post = get_last_approved_item(username)

        if last_text:
            if is_post:
                msg = (
                    f"Hey u/{username} 🌿\n\n"
                    f"It’s been {days_since} days since your post *“{last_text}”*. "
                    "We’d love to hear from you again soon! 🌞"
                )
            else:
                msg = (
                    f"Hey u/{username} 🌿\n\n"
                    f"It’s been {days_since} days since your comment *“{last_text}”*. "
                    "Your voice matters — join the conversation again! ✨"
                )
        else:
            msg = (
                f"Hey u/{username} 🌿\n\n"
                f"It’s been {days_since} days since your last activity. "
                "We’d love to see you back sharing and connecting with everyone! 💚"
            )

        reddit_owner.redditor(username).message(
            f"🌿 A friendly nudge from r/{SUBREDDIT_NAME}", msg
        )
        print(f"📩 Friendly reminder sent to u/{username}")

        # Optional: still log to Discord decay channel
        channel = bot.get_channel(DISCORD_DECAY_LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🌿 Friendly Reminder Sent",
                description=f"u/{username} (inactive {days_since}d, decay in {DECAY_AFTER_DAYS - days_since}d)",
                color=discord.Color.green(),
            )
            embed.add_field(name="Current Karma", value=str(karma), inline=True)
            embed.add_field(name="Flair", value=flair, inline=True)
            if last_text:
                embed.add_field(name="Last Approved", value=last_text[:256], inline=False)
            await channel.send(embed=embed)

    except Exception as e:
        print(f"⚠️ Failed to send friendly reminder for {username}: {e}")

async def send_owner_feedback(username: str, feedback_type: str):
    """Send a personalized feedback DM from OWNER account."""
    try:
        if feedback_type == "1m_feedback":
            subject = f"🌿 Feedback request from r/{SUBREDDIT_NAME}"
            body = (
                f"Hey u/{username}, you've been active in r/{SUBREDDIT_NAME} for a month now! 🌞\n\n"
                "We’d love your feedback: how do you feel about the community so far?\n"
                "Is there anything we could improve, or features you’d like to see? 💬"
            )
        elif feedback_type == "1w_rules":
            subject = f"📜 Quick check-in from r/{SUBREDDIT_NAME}"
            body = (
                f"Hey u/{username}, thanks for being with us for a week! 🌿\n\n"
                "We’re curious — what do you think about our rules and features?\n"
                "Are they clear and supportive, or do you see room for changes? 🤔"
            )
        elif feedback_type == "1w_prompts":
            subject = f"💚 Daily Prompts Check-in"
            body = (
                f"Hey u/{username}, you’ve seen our daily prompts for a week now 🌞\n\n"
                "Do you enjoy them? Would you like more variety (facts, mindfulness, trivia)?\n"
                "Your input helps us keep the community inspiring 🌿"
            )
        else:
            return

        reddit_owner.redditor(username).message(subject, body)
        print(f"📩 Owner feedback DM ({feedback_type}) sent to u/{username}")

        # Optional: log to Discord for mods
        channel = bot.get_channel(DISCORD_DECAY_LOG_CHANNEL_ID)  # reuse decay log or make a new FEEDBACK log channel
        if channel:
            embed = discord.Embed(
                title="📩 Owner Feedback Sent",
                description=f"u/{username} — {feedback_type}",
                color=discord.Color.blurple(),
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"⚠️ Failed to send feedback ({feedback_type}) to u/{username}: {e}")

EN_STOPWORDS = {
    "the","be","to","of","and","a","in","that","have","i","it","for","not",
    "on","with","he","as","you","do","at","this","but","his","by","from","we",
    "say","her","she","or","an","will","my","one","all","would","there","their"
}

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".webp", ".bmp", ".tiff", ".svg")

REDDIT_IMAGE_HOSTS = {"i.redd.it", "i.reddituploads.com"}

async def cahnow(ctx):
    """Force start a CAH round immediately."""
    # check: do we have any cards in enabled packs?
    active = cah_enabled_packs()
    if not active:
        await ctx.send("⚠️ No enabled packs found.")
        return
    total_cards = 0
    for p in active:
        cnt = supabase.table("cah_black_cards").select("id", count="exact").eq("pack_key", p["key"]).execute()
        total_cards += cnt.count or 0
    if total_cards <= 0:
        await ctx.send("⚠️ No black cards available in enabled packs.")
        return

    black = cah_pick_black_card()
    title = "🎲 CAH Round — Fill in the Blank!"
    submission = reddit_owner.subreddit(SUBREDDIT_NAME).submit(title, selftext=f"**Black card:** {black}")
    if CAH_POST_FLAIR_ID:
        try:
            submission.flair.select(CAH_POST_FLAIR_ID)
        except:
            pass
    submission.mod.approve()
    round_id = str(uuid.uuid4())
    start_ts = datetime.utcnow()
    lock_after = start_ts + timedelta(hours=CAH_ROUND_DURATION_H)
    supabase.table("cah_rounds").insert({
        "round_id": round_id,
        "post_id": submission.id,
        "black_text": black,
        "start_ts": start_ts.isoformat(),
        "status": "open",
        "lock_after_ts": lock_after.isoformat()
    }).execute()
    await log_cah_event(
        "🎲 New Round (manual)",
        f"Black card: **{black}**\n[Reddit link](https://reddit.com{submission.permalink})"
    )
    await log_cah_event("🎲 New Round (manual)", f"Black card: **{black}**\n[Reddit link](https://reddit.com{submission.permalink})")
    try:
        await ctx.message.delete()   # ✅ delete your !cahnow message
    except:
        pass

async def _cah_fetch_page(pack_key: str, page: int, page_size: int = CAH_PAGE_SIZE):
    """
    Returns (rows, total_count, total_pages) for a page of black cards in a pack.
    rows: list of dicts with keys id,text
    """
    try:
        # get total
        cnt = supabase.table("cah_black_cards") \
            .select("id", count="exact") \
            .eq("pack_key", pack_key) \
            .execute()
        total = int(cnt.count or 0)
        if total == 0:
            return [], 0, 0

        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        start = (page - 1) * page_size
        end = start + page_size - 1

        rows = supabase.table("cah_black_cards") \
            .select("id, text") \
            .eq("pack_key", pack_key) \
            .order("id", desc=False) \
            .range(start, end) \
            .execute().data or []

        return rows, total, total_pages
    except Exception as e:
        print(f"⚠️ _cah_fetch_page failed: {e}")
        return [], 0, 0

async def _cah_render_page_embed(ctx, pack_key: str, page: int):
    rows, total, total_pages = await _cah_fetch_page(pack_key, page)
    if total == 0:
        return await ctx.send(f"ℹ️ No cards found for pack `{pack_key}`.")

    lines = []
    for r in rows:
        t = (r['text'] or '').replace("\n", " ")
        if len(t) > 120:
            t = t[:117] + "..."
        lines.append(f"`{r['id']}` — {t}")

    embed = discord.Embed(
        title=f"🗂️ Cards in `{pack_key}` — page {page}/{total_pages}",
        description="\n".join(lines) or "—",
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"{total} total cards • use !listcards {pack_key} <page> • remove with !removecard {pack_key} <id>")
    await ctx.send(embed=embed)

async def listcards(ctx, pack_key: str = None, page: str = "1"):
    """Browse all cards in a pack with paging: !listcards <pack_key> [page]"""
    try:
        if DISCORD_CAH_CHANNEL_ID and ctx.channel.id != DISCORD_CAH_CHANNEL_ID:
            return await ctx.send(f"⚠️ Please use this in <#{DISCORD_CAH_CHANNEL_ID}>.")

        if not pack_key:
            return await ctx.send("Usage: `!listcards <pack_key> [page]`")

        if not _cah_pack_exists(pack_key):
            return await ctx.send(f"❌ Unknown pack `{pack_key}`.")

        try:
            p = int(page)
        except ValueError:
            return await ctx.send("⚠️ Page must be a number.")

        await _cah_render_page_embed(ctx, pack_key, p)
    except Exception as e:
        print(f"⚠️ listcards error: {e}")
        await ctx.send("⚠️ Couldn’t list cards right now.")

async def addcard(ctx):
    """Interactive flow to add a CAH black card to Supabase."""
    rows = supabase.table("cah_packs").select("key, name, enabled").execute().data or []
    pack_lines = [
        f"- **{r['key']}** ({r['name']}) → {'ENABLED ✅' if r['enabled'] else 'disabled ❌'}"
        for r in rows
    ]
    embed = discord.Embed(
        title="📝 Add a new CAH Black Card",
        description=(
            "Reply in this channel with:\n\n"
            "`pack_key | card text`\n\n"
            "**Example:**\n"
            "`summer | Nothing says naturism like ____.`\n\n"
            "⚠️ Use `____` for blanks!\n\n"
            "**Available Packs:**\n" + "\n".join(pack_lines)
        ),
        color=discord.Color.blurple()
    )
    prompt_msg = await ctx.send(embed=embed)

    def check(m):
        return m.author == ctx.author and "|" in m.content and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", timeout=120.0, check=check)
        pack_key, card_text = [p.strip() for p in msg.content.split("|", 1)]

        pack = supabase.table("cah_packs").select("*").eq("key", pack_key).execute()
        if not pack.data:
            await ctx.send(f"⚠️ Pack '{pack_key}' not found.")
            return

        if "____" not in card_text:
            await ctx.send("⚠️ Card text must contain at least one `____` blank.")
            return

        res = supabase.table("cah_black_cards").insert({
            "pack_key": pack_key,
            "text": card_text
        }).execute()

        if res.data:
            await log_cah_event("🆕 Card Added", f"Pack: **{pack_key}**\nText: {card_text}")
        else:
            await log_cah_event("⚠️ Add Card Failed", f"Pack: **{pack_key}**\nText: {card_text}")

    except asyncio.TimeoutError:
        await log_cah_event("⌛ Add Card Timeout", f"No reply from {ctx.author.mention}")

    finally:
        # ✅ clean up both prompt + user reply
        try:
            await prompt_msg.delete()
        except:
            pass
        try:
            await msg.delete()
        except:
            pass

async def removecard(ctx, pack_key: str = None, card_id: str = None):
    """
    Remove a card by ID.
    - Direct: !removecard <pack_key> <card_id>
    - Interactive: !removecard  (then follow prompts: pack -> page -> id)
    """
    try:
        if DISCORD_CAH_CHANNEL_ID and ctx.channel.id != DISCORD_CAH_CHANNEL_ID:
            return await ctx.send(f"⚠️ Please use this in <#{DISCORD_CAH_CHANNEL_ID}>.")

        # --- Direct mode ---
        if pack_key and card_id:
            if not _cah_pack_exists(pack_key):
                return await ctx.send(f"❌ Unknown pack `{pack_key}`.")
            try:
                cid = int(card_id)
            except ValueError:
                return await ctx.send("⚠️ card_id must be a number.")

            res = supabase.table("cah_black_cards").delete() \
                .eq("pack_key", pack_key).eq("id", cid).execute()
            if getattr(res, "data", None) is not None:
                await log_cah_event("🗑️ Card Removed", f"Pack: **{pack_key}**\nCard ID: {cid}")
                await ctx.send(f"✅ Deleted card `{cid}` from `{pack_key}`")
            else:
                await ctx.send(f"⚠️ Couldn’t delete card `{cid}` (not found?).")
            return

        # --- Interactive mode ---
        prompt_msg = await ctx.send("📦 Which pack do you want to browse? (type the exact `pack_key`)")

        def check_pack(m): 
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg_pack = await bot.wait_for("message", timeout=60.0, check=check_pack)
        except asyncio.TimeoutError:
            await log_cah_event("⌛ Remove Card Timeout", f"No pack reply from {ctx.author.mention}")
            try: await prompt_msg.delete()
            except: pass
            return

        pack = msg_pack.content.strip()
        if not _cah_pack_exists(pack):
            await ctx.send(f"❌ Unknown pack `{pack}`. Cancelled.")
            try:
                await prompt_msg.delete()
                await msg_pack.delete()
            except: pass
            return

        page = 1
        await _cah_render_page_embed(ctx, pack, page)
        instr_msg = await ctx.send(
            "➡️ Type one of:\n"
            "• a **card ID** to delete\n"
            "• `next` / `prev`\n"
            "• `page <n>` (e.g. `page 3`)\n"
            "• `cancel`"
        )

        while True:
            def check_nav(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                reply = await bot.wait_for("message", timeout=120.0, check=check_nav)
            except asyncio.TimeoutError:
                await log_cah_event("⌛ Remove Card Timeout", f"No reply from {ctx.author.mention}")
                try:
                    await instr_msg.delete()
                    await msg_pack.delete()
                    await prompt_msg.delete()
                except: pass
                return

            content = reply.content.strip().lower()
            if content in ("cancel", "stop", "exit"):
                await ctx.send("❎ Cancelled.")
                try:
                    await instr_msg.delete()
                    await msg_pack.delete()
                    await prompt_msg.delete()
                    await reply.delete()
                except: pass
                return

            if content in ("next", "n", ">"):
                _, total, total_pages = await _cah_fetch_page(pack, page)
                if total_pages == 0:
                    await ctx.send("ℹ️ No cards.")
                    continue
                page = min(page + 1, total_pages)
                await _cah_render_page_embed(ctx, pack, page)
                continue

            if content in ("prev", "p", "<"):
                page = max(1, page - 1)
                await _cah_render_page_embed(ctx, pack, page)
                continue

            if content.startswith("page "):
                try:
                    want = int(content.split()[1])
                except Exception:
                    await ctx.send("⚠️ Usage: `page <number>`")
                    continue
                _, total, total_pages = await _cah_fetch_page(pack, want)
                if total_pages == 0:
                    await ctx.send("ℹ️ No cards.")
                    continue
                page = max(1, min(want, total_pages))
                await _cah_render_page_embed(ctx, pack, page)
                continue

            # otherwise, try to parse as ID and delete
            try:
                cid = int(content)
            except ValueError:
                await ctx.send("⚠️ Not understood. Reply with a card ID, `next`, `prev`, `page <n>`, or `cancel`.")
                continue

            res = supabase.table("cah_black_cards").delete() \
                .eq("pack_key", pack).eq("id", cid).execute()
            if getattr(res, "data", None) is not None:
                await log_cah_event("🗑️ Card Removed", f"Pack: **{pack}**\nCard ID: {cid}")
                await ctx.send(f"✅ Deleted card `{cid}` from `{pack}`")
                # ✅ cleanup
                try:
                    await instr_msg.delete()
                    await msg_pack.delete()
                    await prompt_msg.delete()
                    await reply.delete()
                except: pass
                return
            else:
                await ctx.send(f"⚠️ Couldn’t delete card `{cid}` (not found?). Try again.")

    except commands.MissingPermissions:
        await ctx.send("🚫 You need `Manage Server` to remove cards.")
    except Exception as e:
        print(f"⚠️ removecard error: {e}")
        await ctx.send("⚠️ Couldn’t remove cards right now.")

async def enablepack(ctx, pack_key: str = None):
    """Enable a CAH pack (so its cards can be used)."""
    try:
        if not pack_key:
            return await ctx.send("⚠️ Usage: `!enablepack <pack_key>`")

        res = supabase.table("cah_packs").update({"enabled": True}).eq("key", pack_key).execute()
        if res.data:
            await log_cah_event("📦 Pack Enabled", f"Pack: **{pack_key}**")
        else:
            await log_cah_event("⚠️ Enable Pack Failed", f"Pack: **{pack_key}** not found.")
    finally:
        try:
            await ctx.message.delete()   # ✅ cleanup
        except:
            pass

async def disablepack(ctx, pack_key: str = None):
    """Disable a CAH pack (its cards won’t be picked)."""
    try:
        if not pack_key:
            return await ctx.send("⚠️ Usage: `!disablepack <pack_key>`")

        res = supabase.table("cah_packs").update({"enabled": False}).eq("key", pack_key).execute()
        if res.data:
            await log_cah_event("📦 Pack Disabled", f"Pack: **{pack_key}**")
        else:
            await log_cah_event("⚠️ Disable Pack Failed", f"Pack: **{pack_key}** not found.")
    finally:
        try:
            await ctx.message.delete()   # ✅ cleanup
        except:
            pass

async def listpacks(ctx):
    """List all CAH packs with their enabled/disabled status."""
    try:
        rows = supabase.table("cah_packs").select("key, name, enabled").execute().data or []
        if not rows:
            return await ctx.send("⚠️ No packs found in Supabase.")

        lines = [
            f"- **{r['key']}** ({r['name']}) → {'✅ ENABLED' if r['enabled'] else '❌ disabled'}"
            for r in rows
        ]

        embed = discord.Embed(
            title="📦 Available CAH Packs",
            description="\n".join(lines),
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

        # delete command message to keep channel clean
        try:
            await ctx.message.delete()
        except:
            pass

    except Exception as e:
        await ctx.send(f"⚠️ Error fetching packs: {e}")

COMMANDS = {
    "!stats": cmd_stats,
    "!flairlist": cmd_flairlist,
    "!rules": cmd_rules,
    "!decay": cmd_decay,
    "!top": cmd_top,
    "!safety": cmd_safety,
    "!observer": cmd_observer,
    "!help": cmd_help,
    "!recount": cmd_recount,
}

KEYWORD_MAP = parse_keyword_map(POST_FLAIR_KEYWORDS)

async def _lock_and_delete_message(msg: discord.Message):
    """Decision lock: mark as LOCKED, clear reactions, then delete after a short delay."""
    try:
        embed = msg.embeds[0] if msg.embeds else None
        if embed:
            if embed.title and "🔒" not in embed.title:
                embed.title = f"🔒 {embed.title} (LOCKED)"
            embed.color = discord.Color.dark_grey()
            await msg.edit(embed=embed)
        await msg.clear_reactions()
    except Exception:
        pass
    await asyncio.sleep(2)
    try:
        await msg.delete()
    except Exception:
        pass

async def send_discord_approval(item, lang_label=None, note=None, night_guard_ping=False, priority_level:int=0):
    """Send item to Discord for manual review; optional Night Guard ping; supports PRIORITY levels + ETA."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("⚠️ Discord channel not found")
        return

    author = str(item.author)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    if hasattr(item, "title"):
        content = f"**{item.title}**\n\n{item.selftext or ''}"
        item_type = "Post"
        img_label = image_flag_label(item)
    else:
        content = item.body or ""
        item_type = "Comment"
        img_label = "N/A"

    # === Title prefix handling ===
    title_prefix = f"{SLA_PRIORITY_PREFIX} (L{priority_level}) · " if priority_level > 0 else ""
    if note and "Restored" in note:
        title_prefix = "🔴 (RESTORED) · " + title_prefix

    embed = discord.Embed(
        title=f"{title_prefix}🧾 {item_type} Pending Review",
        description=(content[:4000] + ("... (truncated)" if len(content) > 4000 else "")),
        color=discord.Color.orange() if priority_level == 0 else discord.Color.red(),
    )
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    if lang_label:
        embed.add_field(name="Language", value=lang_label, inline=True)
    if note:
        embed.add_field(name="Note", value=note, inline=False)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    # === Rules overview ===
    rules_overview = "\n".join([f"{emoji} {text}" for emoji, text in REJECTION_REASONS.items()])
    embed.add_field(name="Rules Overview", value=rules_overview[:1024], inline=False)

    # === ETA footer (NEW) ===
    eta_text = compute_eta_text(pending_count=len(pending_reviews) + 1)
    embed.set_footer(text=f"Queue ETA: {eta_text}")

    mention = ""
    if night_guard_ping and MOD_PING_ROLE_ID:
        global _last_mod_ping_ts
        now = time.time()
        if now - _last_mod_ping_ts >= MOD_PING_COOLDOWN_SEC:
            mention = f"<@&{MOD_PING_ROLE_ID}> "
            _last_mod_ping_ts = now

    msg = await channel.send(content=mention.strip() or None, embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    await msg.add_reaction("🔄")

    pending_reviews[msg.id] = {
        "item": item,
        "created_ts": time.time() if priority_level == 0 else (time.time() - SLA_MINUTES * 60 * priority_level),
        "last_escalated_ts": time.time(),
        "level": priority_level,
    }
    save_pending_review(msg.id, item, priority_level)
    print(f"📨 Sent {item_type} by u/{author} to Discord (priority={priority_level}, ETA={eta_text}, night_ping={bool(mention)})")

async def send_discord_auto_log(item, old_k, new_k, flair, awarded_points, extras_note=""):
    channel = bot.get_channel(DISCORD_AUTO_APPROVAL_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_AUTO_APPROVAL_CHANNEL_ID)
        except Exception:
            return
    
    author = str(item.author)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)

    embed = discord.Embed(
        title=f"✅ Auto-approved {item_type}",
        description=(content[:1000] + ("... (truncated)" if len(content) > 1000 else "")),
        color=discord.Color.green(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k}  (+{awarded_points})", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    if extras_note:
        embed.add_field(name="Notes", value=extras_note, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)
    await channel.send(embed=embed)

async def log_approval(item, old_k: int, new_k: int, flair: str, note: str, extras: str = ""):
    """Log full approval info to the approval log channel."""
    channel = bot.get_channel(DISCORD_APPROVAL_LOG_CHANNEL_ID)
    if not channel:
        return

    author = str(item.author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    embed = discord.Embed(
        title=f"✅ Approved {item_type}",
        description=(content[:1500] + ("... (truncated)" if len(content) > 1500 else "")),
        color=discord.Color.green(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k} {note}", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    if extras:
        embed.add_field(name="Notes", value=extras, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    await channel.send(embed=embed)

async def log_rejection(item, old_k: int, new_k: int, flair: str, reason_text: str):
    """Log full rejection info (with reason) to the rejection log channel."""
    channel = bot.get_channel(DISCORD_REJECTION_LOG_CHANNEL_ID)
    if not channel:
        return

    author = str(item.author)
    item_type = "Post" if hasattr(item, "title") else "Comment"
    content = (item.selftext if hasattr(item, "selftext") else item.body) or ""
    img_label = image_flag_label(item)
    sub_karma, acct_days = about_user_block(author)
    shadow = get_shadow_flag(author)

    embed = discord.Embed(
        title=f"❌ Rejected {item_type}",
        description=(content[:1500] + ("... (truncated)" if len(content) > 1500 else "")),
        color=discord.Color.red(),
    )
    if hasattr(item, "title") and item.title:
        embed.add_field(name="Title", value=item.title[:256], inline=False)
    embed.add_field(name="Author", value=f"u/{author}", inline=True)
    embed.add_field(name="Reason", value=reason_text, inline=False)   # 👈 NEW
    embed.add_field(name="Image", value=img_label, inline=True)
    embed.add_field(name="Karma", value=f"{old_k} → {new_k} (−1)", inline=True)
    embed.add_field(name="Flair", value=flair, inline=True)
    embed.add_field(name="Sub Karma", value=str(sub_karma), inline=True)
    embed.add_field(name="Acct Age (days)", value=str(acct_days), inline=True)
    if shadow:
        embed.add_field(name="Shadow Flag", value=shadow, inline=False)
    embed.add_field(name="Link", value=f"https://reddit.com{item.permalink}", inline=False)

    await channel.send(embed=embed)

async def log_achievement(username: str, badge_name: str):
    """Send an achievement unlock to the Achievements Discord channel."""
    channel = bot.get_channel(DISCORD_ACHIEVEMENTS_CHANNEL_ID)
    if not channel:
        print("⚠️ Achievements channel not found")
        return

    embed = discord.Embed(
        title="🌟 New Achievement Unlocked",
        description=f"u/{username} → **{badge_name}**",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)   # 👈 aware timestamp
    )
    await channel.send(embed=embed)

async def log_cah_event(title:str, desc:str, color=discord.Color.blurple()):
    if not DISCORD_CAH_CHANNEL_ID: return
    channel=bot.get_channel(DISCORD_CAH_CHANNEL_ID)
    if not channel:
        try: channel=await bot.fetch_channel(DISCORD_CAH_CHANNEL_ID)
        except: return
    embed=discord.Embed(title=title,description=desc,color=color,timestamp=datetime.now(timezone.utc))
    await channel.send(embed=embed)

async def prompt_pack_toggle(pack_key: str, action: str, when: str):
    """
    Prompt in Discord CAH channel to enable/disable a pack.
    action = 'enable' or 'disable'
    when = human-readable date (e.g. 'Dec 1')
    """
    channel = bot.get_channel(DISCORD_CAH_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(DISCORD_CAH_CHANNEL_ID)
        except Exception:
            return

    embed = discord.Embed(
        title=f"📦 {pack_key.title()} Pack {action.capitalize()}?",
        description=f"The **{pack_key.title()}** pack is scheduled to {action} on **{when}**.\n\n"
                    f"React ✅ to {action}, ❌ to skip.",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)
    )
    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            reaction.message.id == msg.id
            and not user.bot
            and str(reaction.emoji) in ["✅", "❌"]
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=86400.0, check=check)
        if str(reaction.emoji) == "✅":
            if action == "enable":
                supabase.table("cah_packs").update({"enabled": True}).eq("key", pack_key).execute()
                await log_cah_event("📦 Pack Enabled", f"Pack: **{pack_key}**")
            else:
                supabase.table("cah_packs").update({"enabled": False}).eq("key", pack_key).execute()
                await log_cah_event("📦 Pack Disabled", f"Pack: **{pack_key}**")
        else:
            await log_cah_event("⏳ Pack Change Skipped", f"Pack: **{pack_key}** left unchanged.")

        # ✅ Clean up the original prompt
        try:
            await msg.delete()
        except Exception:
            pass

    except asyncio.TimeoutError:
        await log_cah_event("⌛ No Response", f"Pack: **{pack_key}** unchanged.")
        try:
            await msg.delete()
        except Exception:
            pass

async def _escalate_card(msg_id: int):
    entry = pending_reviews.get(msg_id)
    if not entry:
        return
    item = entry["item"]
    level = entry.get("level", 0) + 1

    # delete old message if still exists
    try:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        old_msg = await channel.fetch_message(msg_id)
        await old_msg.delete()
    except Exception:
        pass

    # re-post with higher priority marker (ETA recalculated inside)
    await send_discord_approval(
        item,
        lang_label="English",
        note=f"{SLA_PRIORITY_PREFIX}: waiting > {level * SLA_MINUTES} minutes",
        night_guard_ping=False,
        priority_level=level,
    )

async def on_ready():
    print(f"🤖 Discord bot logged in as {bot.user}")
    # Restore reviews from Supabase
    restore_pending_reviews()
    threading.Thread(target=reddit_polling, daemon=True).start()
    threading.Thread(target=reddit_dm_polling, daemon=True).start()
    threading.Thread(target=decay_loop, daemon=True).start()
    threading.Thread(target=sla_loop, daemon=True).start()
    threading.Thread(target=daily_prompt_poster, daemon=True).start()
    threading.Thread(target=daily_fact_poster, daemon=True).start()
    threading.Thread(target=feedback_loop, daemon=True).start()
    threading.Thread(target=weekly_achievements_loop, daemon=True).start()
    threading.Thread(target=upvote_reward_loop, daemon=True).start()
    threading.Thread(target=cah_loop, daemon=True).start()
    threading.Thread(target=pack_schedule_loop, daemon=True).start()

async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    print(f"➡️ Reaction received: {reaction.emoji} by {user} on msg {msg_id}")

    # Check if the message is still tracked
    if msg_id not in pending_reviews:
        print("⚠️ Reaction on stale card.")

        # If moderator clicked refresh, try to rebuild and repost the card
        if str(reaction.emoji) == "🔄":
            link = _get_permalink_from_embed(reaction.message)
            if not link:
                await reaction.message.channel.send("⚠️ I can't find the original link on this card.")
                return
            item = _fetch_item_from_permalink(link)
            if not item:
                await reaction.message.channel.send("⚠️ I couldn't reconstruct the original item from the link.")
                return
            if already_moderated(item):
                await reaction.message.channel.send("ℹ️ This item is already moderated — no need to refresh.")
                return

            # Repost a fresh card at base priority with a note
            await send_discord_approval(
                item,
                lang_label="English",
                note="↻ Refreshed stale card",
                night_guard_ping=False,
                priority_level=0,
            )
            try:
                await reaction.message.delete()
            except Exception:
                pass
            return

        # For ✅/❌ on stale cards, guide moderator to use 🔄
        await reaction.message.channel.send("⛔ This review card is no longer active. Click 🔄 on the card to refresh it.")
        return

    entry = pending_reviews.pop(msg_id, None)
    delete_pending_review(msg_id)
    if not entry:
        print("⚠️ Entry missing even though msg_id was in pending_reviews.")
        return

    item = entry["item"]
    author_name = str(item.author)

    # 🔄 REFRESH (repost the same item, keep the current priority level)
    if str(reaction.emoji) == "🔄":
        level = entry.get("level", 0)
        await send_discord_approval(
            item,
            lang_label="English",
            note="↻ Manual refresh",
            night_guard_ping=False,
            priority_level=level,
        )
        await _lock_and_delete_message(reaction.message)
        print(f"🔄 Card refreshed for u/{author_name} (level={level})")
        return

    try:
        # ✅ APPROVE
        if str(reaction.emoji) == "✅":
            print(f"✅ Approving u/{author_name}...")
            item.mod.approve()
            old_k, new_k, flair, total_delta, extras = apply_approval_awards(item, is_manual=True)
            note = f"+{total_delta}" + (f" ({extras})" if extras else "")

            await reaction.message.channel.send(
                f"✅ Approved u/{author_name} ({old_k} → {new_k}) {note}, flair: {flair}"
            )
            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)
            await log_approval(item, old_k, new_k, flair, note, extras)
            print(f"✅ Approval done for u/{author_name}")

        # ❌ REJECT
        elif str(reaction.emoji) == "❌":
            print(f"❌ Rejecting u/{author_name}...")
            item.mod.remove()
            old_k, new_k, flair = apply_karma_and_flair(item.author, -1, allow_negative=True)

            await reaction.message.channel.send(
                f"❌ Removed u/{author_name}'s item ({old_k} → {new_k}), flair: {flair}."
            )

            # Add rule reactions to pick rejection reason
            review_msg = reaction.message
            for emoji in REJECTION_REASONS.keys():
                await review_msg.add_reaction(emoji)

            def check(r, u):
                return (
                    r.message.id == review_msg.id
                    and u.id == user.id
                    and str(r.emoji) in REJECTION_REASONS
                )

            try:
                reason_reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reason_reaction.emoji) == "✏️":
                    prompt_msg = await reaction.message.channel.send(
                        f"{user.mention}, please type the custom rejection reason (60s timeout):"
                    )
                    msg = await bot.wait_for(
                        "message",
                        timeout=60.0,
                        check=lambda m: m.author == user and m.channel == reaction.message.channel
                    )
                    reason_text = f"Custom: {msg.content}"
                    try:
                        await prompt_msg.delete()
                        await msg.delete()
                    except Exception as e:
                        print(f"⚠️ Could not delete custom reason messages: {e}")
                else:
                    reason_text = REJECTION_REASONS[str(reason_reaction.emoji)]

                # DM Reddit user
                try:
                    redditor = reddit.redditor(author_name)
                    redditor.message(
                        f"❌ Your post/comment was removed from r/{SUBREDDIT_NAME}",
                        f"Reason: {reason_text}\n\nPlease review the subreddit rules before posting again."
                    )
                    print(f"📩 Sent rejection DM to u/{author_name}")
                except Exception as e:
                    print(f"⚠️ Could not DM u/{author_name}: {e}")

                # Log rejection
                await log_rejection(item, old_k, new_k, flair, reason_text)
                print(f"❌ Rejection logged for u/{author_name}")

            except asyncio.TimeoutError:
                await reaction.message.channel.send("⏳ No rejection reason chosen, skipping DM/log reason.")
                print("⚠️ Timeout waiting for rejection reason.")

            record_mod_decision(entry.get("created_ts"), user.id)
            await _lock_and_delete_message(reaction.message)

        else:
            print(f"ℹ️ Ignored reaction {reaction.emoji} (not ✅ or ❌).")

    except Exception as e:
        print(f"🔥 Error handling reaction {reaction.emoji} for u/{author_name}: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
