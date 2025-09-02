"""
Polling loop for pending marker edit/delete approvals.
"""

import time, asyncio, discord
from app.clients.supabase import supabase
from app.clients.discord_bot import bot
from app.models.state import pending_marker_actions
from app.config import DISCORD_CHANNEL_ID

async def _send_action(row):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return None
    action = row.get("action")
    user = row.get("username", "unknown")
    name = row.get("name", "")
    country = row.get("country", "")
    category = row.get("category", "")
    title = "Marker Delete Request" if action == "delete" else "Marker Edit Request"
    desc = f"{name}, {country} ({category}) by {user}"
    embed = discord.Embed(title=title, description=desc, color=discord.Color.orange())
    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    return msg

def marker_actions_loop():
    while True:
        try:
            rows = supabase.table("pending_marker_actions").select("*").execute().data or []
            for row in rows:
                msg_id = row.get("discord_msg_id")
                if not msg_id:
                    fut = asyncio.run_coroutine_threadsafe(_send_action(row), bot.loop)
                    msg = fut.result()
                    if msg:
                        supabase.table("pending_marker_actions").update({"discord_msg_id": msg.id}).eq("id", row["id"]).execute()
                        pending_marker_actions[msg.id] = row
                else:
                    pending_marker_actions[msg_id] = row
        except Exception as e:
            print(f"⚠️ marker_actions_loop error: {e}")
        time.sleep(30)