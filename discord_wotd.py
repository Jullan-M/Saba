# bot.py
import os
import asyncio
import discord
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Target channel

client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@tasks.loop(hours=24)
async def called_once_a_day():
    message_channel = client.get_channel(CHANNEL_ID)
    print(f"Got channel {message_channel}")
    await message_channel.send("Your message")


@called_once_a_day.before_loop
async def before():
    await client.wait_until_ready()
    print("Finished waiting")

called_once_a_day.start()
client.run(TOKEN)
