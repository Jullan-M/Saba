# bot.py
import os
import asyncio
import discord
import datetime
from discord.ext import tasks
from dotenv import load_dotenv
from wotd import word_of_the_day
from Word import Word, Meaning, Translation

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Target channel
WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))

FLAG = {'nb': '🇳🇴',
        'nob': '🇳🇴',
        'sv': '🇸🇪',
        'fi': '🇫🇮',
        'fin': '🇫🇮',
        'en': '🇬🇧',
        'smn': '<:heillt:725006488476581950>',
        'se': 'se'}


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


def wotd_message(word):
    intro = f"Otná sátni lea **{word}**!\n Sánis leat {len(word.meanings)} mearkkašumit:\n"
    main = ""
    for i, m in enumerate(word.meanings):
        main += f"\t__{i+1}. ({m.pos})__\n"
        for tr in m.trs:
            main += f"\t\t{FLAG[tr.lang]} {tr}\n"
            for ex in tr.examples:
                print(ex)
                main += f"> *{ex[0]}*\n> *{ex[1]}*\n"
    return intro + main


client = discord.Client()


@tasks.loop(seconds=30)
async def called_once_a_day():
    print("Fetching word of the day")
    word = word_of_the_day('smenob')
    print("Today's word is:", word)
    print("Generating message...")
    wotd = wotd_message(word)
    message_channel = client.get_channel(CHANNEL_ID)
    print(f"Got channel {message_channel}")
    await message_channel.send(wotd)


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
