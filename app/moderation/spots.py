"""Moderation helpers for nudist spot submissions."""

import os
import time
import discord
from dotenv import load_dotenv
from app.clients.discord_bot import bot
from app.clients.supabase import supabase
from app.clients.reddit_bot import reddit
from app.models.state import pending_spots
from app.models.spot import SpotSubmission

load_dotenv()

discord_spots_channel_id_str = os.getenv("DISCORD_SPOTS_CHANNEL_ID")
try:
    DISCORD_SPOTS_CHANNEL_ID = int(discord_spots_channel_id_str)
except (TypeError, ValueError):
    DISCORD_SPOTS_CHANNEL_ID = 0
    if discord_spots_channel_id_str is None:
        print("⚠️ DISCORD_SPOTS_CHANNEL_ID not set; defaulting to 0")
    else:
        print(
            f"⚠️ Invalid DISCORD_SPOTS_CHANNEL_ID '{discord_spots_channel_id_str}'; defaulting to 0"
        )


async def send_spot_submission(spot: SpotSubmission) -> None:
    """Send a spot submission to the Discord moderation channel."""
    channel = bot.get_channel(DISCORD_SPOTS_CHANNEL_ID)
    if not channel:
        print("⚠️ Spots channel not found")
        return

    embed = discord.Embed(
        title="📍 Spot Submission",
        description=spot.description or "No description provided.",
        color=discord.Color.blue(),
    )
    embed.add_field(name="Name", value=spot.name, inline=True)
    embed.add_field(
        name="Coordinates", value=f"{spot.latitude}, {spot.longitude}", inline=True
    )
    embed.add_field(name="Official", value="Yes" if spot.official else "No", inline=True)
    embed.set_footer(text=f"Submitted by u/{spot.submitted_by}")

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    pending_spots[msg.id] = {"spot": spot, "created_ts": time.time()}
    print(f"📨 Spot '{spot.name}' queued for moderation")


async def approve_spot(message: discord.Message, reviewer: discord.User, spot: SpotSubmission) -> None:
    """Insert approved spot into Supabase and notify submitter."""
    try:
        supabase.table("spots").insert(
            {
                "name": spot.name,
                "latitude": spot.latitude,
                "longitude": spot.longitude,
                "official": spot.official,
                "description": spot.description,
                "submitted_by": spot.submitted_by,
                "approved_by": str(reviewer),
            }
        ).execute()
        try:
            reddit.redditor(spot.submitted_by).message(
                "✅ Spot Approved",
                f"Your nudist spot '{spot.name}' was approved. Thanks for contributing!",
            )
        except Exception:
            pass
        await message.channel.send(
            f"✅ Spot '{spot.name}' approved by {reviewer.mention}"
        )
    except Exception as e:
        await message.channel.send(f"⚠️ Failed to save spot '{spot.name}': {e}")
    finally:
        try:
            await message.delete()
        except Exception:
            pass


async def reject_spot(message: discord.Message, reviewer: discord.User, spot: SpotSubmission) -> None:
    """Reject a spot submission and notify submitter."""
    try:
        reddit.redditor(spot.submitted_by).message(
            "❌ Spot Rejected",
            f"Your nudist spot '{spot.name}' was rejected by the moderators.",
        )
    except Exception:
        pass
    await message.channel.send(
        f"❌ Spot '{spot.name}' rejected by {reviewer.mention}"
    )
    try:
        await message.delete()
    except Exception:
        pass