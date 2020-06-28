import os
import asyncio
import discord
import datetime
from discord.ext import tasks
from dotenv import load_dotenv
from googletrans import Translator
from wotd import word_of_the_day, FLAG, WORDCLASS, EXCL_LANG

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Target channel
ROLE_ID = int(os.getenv('ROLE_ID'))
WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))


def underscore_word(string, word):
    return string.replace(word.capitalize(), f'__{word.capitalize()}__').replace(word, f'__{word}__')


def wotd_message(word):

    trns = Translator()
    main = ""
    lastpos = ""
    lastword = ""
    lastdesc = ""
    i = 0
    for m in word.meanings:
        trs_text = ""
        for tr in m.trs:
            if tr.lang in EXCL_LANG or (lastword == str(tr) and lastdesc == tr.desc):
                continue
            lastword = str(tr)
            lastdesc = tr.desc

            if tr.lang == 'nob':
                tr_en = trns.translate(str(tr), src='no', dest='en').text
                desc_en = trns.translate(
                    tr.desc, src='no', dest='en').text if tr.desc else ''
                trs_text += f"\t\t{FLAG[tr.lang]} {tr} {tr.desc}\t→\t{FLAG['en']} {tr_en} {desc_en}\n"
                for n, ex in enumerate(tr.examples):
                    ex_en = trns.translate(ex[1], src='no', dest='en').text
                    trs_text += f"> <:samiflag:725121267933511742> *{underscore_word(ex[0], str(word))}*\n"
                    trs_text += f"> {FLAG[tr.lang]} *{underscore_word(ex[1], str(tr))}*\n"
                    trs_text += f"> {FLAG['en']} *{underscore_word(ex_en, tr_en)}*\n"
                    if (n != len(tr.examples)-1):
                        trs_text += "\n"
            else:
                trs_text += f"\t\t{FLAG[tr.lang]} {tr}\n"
        if lastpos != m.pos and trs_text:
            i += 1
            main += f"\t{i}. {WORDCLASS[m.pos]}\n"
            lastpos = m.pos
        main += trs_text

    intro = f"<@&{ROLE_ID}>, otná sátni lea **{word}**!\n Sánis lea"
    intro = intro + \
        f"t {i} mearkkašumit:\n" if (
            i > 1) else intro + f" okta mearkkašupmi:\n"
    return intro + main


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
    now = datetime.datetime.now()
    print(f"Fetching word of the day for\t{now}")
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
