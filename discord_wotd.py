# bot.py
import os
import asyncio
import discord
import datetime
from discord.ext import tasks
from dotenv import load_dotenv
from googletrans import Translator
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
        'smn': 'smn',
        'sma': 'sma',
        'smj': 'smj',
        'sms': 'sms',
        'se': 'se',
        'lat': 'lat'}

WORDCLASS = {'N': 'Substantiiva',
             'V': 'Vearba',
             'Adv': 'Advearba',
             'A': 'Adjektiiva',
             'Pron': 'Pronomen',
             'CC': 'Konjunkšuvdna',
             'Po': 'Postposišuvdna',
             'Pr': 'Preposišuvdna'}

SAMI_LANG = ['smn', 'sma', 'smj', 'sms', 'se']


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
        if lastpos != m.pos:
            i += 1
            main += f"\t{i}. {WORDCLASS[m.pos]}\n"
            lastpos = m.pos

        for tr in m.trs:
            if tr.lang in SAMI_LANG or (lastword == str(tr) and lastdesc == tr.desc):
                continue
            lastword = str(tr)
            lastdesc = tr.desc

            if tr.lang in ['nob', 'nb']:
                tr_en = trns.translate(str(tr), src='no', dest='en').text
                desc_en = trns.translate(
                    tr.desc, src='no', dest='en').text if tr.desc else ''
                main += f"\t\t{FLAG[tr.lang]} {tr} {tr.desc}\t→\t{FLAG['en']} {tr_en} {desc_en}\n"
                for n, ex in enumerate(tr.examples):
                    ex_en = trns.translate(ex[1], src='no', dest='en').text
                    main += f"> <:samiflag:725121267933511742> *{underscore_word(ex[0], str(word))}*\n"
                    main += f"> {FLAG[tr.lang]} *{underscore_word(ex[1], str(tr))}*\n"
                    main += f"> {FLAG['en']} *{underscore_word(ex_en, tr_en)}*\n"
                    if (n != len(tr.examples)-1):
                        main += "\n"
            else:
                main += f"\t\t{FLAG[tr.lang]} {tr}\n"

    intro = f"<@&418533166878425103>, otná sátni lea **{word}**!\n Sánis lea"
    intro = intro + \
        f"t {i} mearkkašumit:\n" if (
            i > 1) else intro + f" okta mearkkašupmi:\n"
    return intro + main


#print(wotd_message(Word('áššáiguoskevaš', 'sme')))

client = discord.Client()


@tasks.loop(seconds=30)
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
