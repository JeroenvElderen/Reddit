import discord
from discord.ext import commands
from app.config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.dm_messages = True
intents.reactions = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
