import os
import asyncio
import discord
import datetime
from discord.ext import tasks
import json
from dotenv import load_dotenv
from googletrans import Translator
from wotd import word_of_the_day, FLAG, WORDCLASS, EXCL_LANG
from utilities import waittime_between

load_dotenv(dotenv_path='wotd_discord/.env')
TOKEN = os.getenv('DISCORD_TOKEN')
SAMIFLAG_ID = int(os.getenv('SAMIFLAG_ID'))
WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))


def underscore_word(string, word):
    if ', ' in word:
        words = word.split(', ')
        sentence = string
        for w in words:
            sentence = sentence.replace(
                w.capitalize(), f'__{w.capitalize()}__').replace(w, f'__{w}__')
        return sentence
    elif ' ' in word:
        words = word.split(' ')
        sentence = string
        for w in words:
            sentence = sentence.replace(
                w.capitalize(), f'__{w.capitalize()}__').replace(w, f'__{w}__')
        return sentence

    return string.replace(word.capitalize(), f'__{word.capitalize()}__').replace(word, f'__{word}__')


class WotdManager:
    def __init__(self, d):
        self.lang = d[:3]
        self.dict = d
        with open("language_conf.json", "r") as f:
            lang_conf = json.load(f)[self.lang]
        self.excl_lang = lang_conf["excl_lang"]
        self.wordclass = lang_conf["wordclass"]
        self.cha_id = int(os.getenv(f'{self.lang}_CHANNEL_ID'))
        self.role_id = int(os.getenv(f'{self.lang}_ROLE_ID'))

    def get_intro_message(self, word, count):
        if self.lang == 'sme':
            intro = f"<@&{self.role_id}>, otná sátni lea **{word}**!\n Sánis lea"
            intro = intro + \
                f"t {count} mearkkašumit:\n" if (
                    count > 1) else intro + f" okta mearkkašupmi:\n"
            return intro

        elif self.lang == 'sma':
            intro = f"<@&{self.role_id}>, dan biejjie baakoe lea **{word}**!\n Sánis lea"
            intro = intro + \
                f"t {count} mearkkašumit:\n" if (
                    count > 1) else intro + f" okta mearkkašupmi:\n"
            return intro

    def get_wotd(self):
        return word_of_the_day(self.dict, 'wotd_discord/')

    def wotd_message(self, word):

        trns = Translator()
        main = ""
        lastpos = ""
        lastword = ""
        lastdesc = ""
        i = 0
        for m in word.meanings:
            trs_text = ""
            for tr in m.trs:
                if tr.lang in self.excl_lang or (lastword == str(tr) and lastdesc == tr.desc):
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
                        trs_text += f"> <:samiflag:{SAMIFLAG_ID}> *{underscore_word(ex[0], str(word))}*\n"
                        trs_text += f"> {FLAG[tr.lang]} *{underscore_word(ex[1], str(tr))}*\n"
                        trs_text += f"> {FLAG['en']} *{underscore_word(ex_en, tr_en)}*\n"
                        if (n != len(tr.examples)-1):
                            trs_text += "\n"
                else:
                    trs_text += f"\t\t{FLAG[tr.lang]} {tr}\n"
            if lastpos != m.pos and trs_text:
                i += 1
                main += f"\t{i}. {self.wordclass[m.pos]}\n"
                lastpos = m.pos
            main += trs_text
        intro = self.get_intro_message(word, i)
        return intro + main


wotd_m = [WotdManager(d) for d in ['smenob', 'smanob']]
client = discord.Client()


@tasks.loop(hours=24)
async def called_once_a_day():
    now = datetime.datetime.now()
    print(f"Fetching wotds for\t{now}")
    for m in wotd_m:
        word = m.get_wotd()
        print(f"{m.lang}-wotd: {word}", end="\t")
        wotd = m.wotd_message(word)
        message_channel = client.get_channel(m.cha_id)
        await message_channel.send(wotd)
        print(f"Sent to {message_channel}!")
    print("Sleeping for 24h\n")


@called_once_a_day.before_loop
async def before():
    await client.wait_until_ready()
    print(f'Finished waiting client. {client.user} has connected to Discord!')
    now = datetime.datetime.now()
    print(f"Time is currently \t{now}.")
    sleeptime = waittime_between(now, WOTD_H, WOTD_M, WOTD_S)
    print(
        f"WOTD is scheduled at \t{WOTD_H}H {WOTD_M}M {WOTD_S}S.")
    for w in wotd_m:
        print(w.lang, client.get_channel(w.cha_id))
    print(f"Sleeptime: \t\t{datetime.timedelta(seconds=sleeptime)}")
    await asyncio.sleep(sleeptime)

called_once_a_day.start()
client.run(TOKEN)
