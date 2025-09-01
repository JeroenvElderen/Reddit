import json
import asyncio
from urllib.parse import quote

import requests
import discord

from app.clients.discord_bot import bot
from app.config import GOOGLE_MAPS_API_KEY, LEGAL_MAP_CHANNEL_ID, LEGAL_MAP_MARKERS_PATH

async def _geocode(name: str, country: str):
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set")
    q = quote(f"{name} {country}")
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={q}&key={GOOGLE_MAPS_API_KEY}"
    loop = asyncio.get_running_loop()
    def fetch():
        res = requests.get(url, timeout=10)
        data = res.json()
        loc = data["results"][0]["geometry"]["location"]
        return [loc["lng"], loc["lat"]]

    return await loop.run_in_executor(None, fetch)

def _save_marker(marker):
    try:
        with LEGAL_MAP_MARKERS_PATH.open() as f:
            markers = json.load(f)
    except FileNotFoundError:
        markers = []
    markers.append(marker)
    with LEGAL_MAP_MARKERS_PATH.open("w") as f:
        json.dump(markers, f, indent=2)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        parts = [p.strip() for p in message.content.split(",")]
        if len(parts) >= 2:
            name, country = parts[:2]
            category = parts[2].lower() if len(parts) >= 3 else "unofficial"
            description = parts[3] if len(parts) >= 4 else ""
            if category not in {"official", "restricted", "unofficial", "illegal"}:
                category = "unofficial"
            try:
                coords = await _geocode(name, country)
                marker = {
                    "name": name,
                    "country": country,
                    "category": category,
                    "coordinates": coords,
                    "description": description,
                }
                _save_marker(marker)
                if LEGAL_MAP_CHANNEL_ID:
                    channel = bot.get_channel(LEGAL_MAP_CHANNEL_ID)
                    if channel:
                        await channel.send(f"New marker: {name}, {country}, {category}")
                await message.channel.send(f"✅ Added marker for {name}, {country} ({category})")
            except Exception as e:
                await message.channel.send(f"❌ Failed to add marker: {e}")
    await bot.process_commands(message)