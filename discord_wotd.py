import os
import asyncio
import discord
import datetime
from discord.ext import tasks
from dotenv import load_dotenv
from wotd import word_of_the_day, wotd_message

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Target channel
WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))


def waittime_from(time):
    base = 86400
    h = time.hour - WOTD_H
    m = time.minute - WOTD_M
    s = time.second - WOTD_S
    diff = h * 3600 + m * 60 + s
    if diff < 0:
        return abs(diff)
    else:
        return base - diff


client = discord.Client()


@tasks.loop(hours=24)
async def called_once_a_day():
    print("Fetching word of the day")
    word = word_of_the_day('smenob')
    print("Today's word is:", word)
    print("Generating message...")
    wotd = wotd_message(word)
    message_channel = client.get_channel(CHANNEL_ID)
    await message_channel.send(wotd)

    print(f"WOTD was sent to {message_channel}.\n")


@called_once_a_day.before_loop
async def before():
    await client.wait_until_ready()
    print(f'Finished waiting client. {client.user} has connected to Discord!')
    now = datetime.datetime.now()
    print(f"Time is currently \t{now}.")
    sleeptime = waittime_from(now)
    print(f"WOTD is scheduled at \t{WOTD_H}H {WOTD_M}M {WOTD_S}S.")
    print(f"Sleeping for \t\t{datetime.timedelta(seconds=sleeptime)} HH:MM:SS")
    await asyncio.sleep(sleeptime)

called_once_a_day.start()
client.run(TOKEN)
