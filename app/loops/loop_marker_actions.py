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

    if action == "edit":
        marker_id = row.get("marker_id")
        try:
            old_row = (
                supabase.table("map_markers")
                .select("name, country, category, coordinates, description")
                .eq("id", marker_id)
                .execute()
                .data
                or []
            )
            old_row = old_row[0] if old_row else {}
        except Exception:
            old_row = {}

        changes = []
        for field, label in [
            ("name", "Name"),
            ("country", "Country"),
            ("category", "Category"),
            ("coordinates", "Coordinates"),
            ("description", "Description"),
        ]:
            new_val = row.get(field)
            old_val = old_row.get(field)
            if str(new_val) != str(old_val):
                new_str = str(new_val) if new_val is not None else ""
                old_str = str(old_val) if old_val is not None else ""
                if label == "Description":
                    new_str = new_str[:500]
                    old_str = old_str[:500]
                changes.append(f"**{label}:** {old_str or '—'} → {new_str or '—'}")

        if changes:
            embed.add_field(name="Updates", value="\n".join(changes), inline=False)

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