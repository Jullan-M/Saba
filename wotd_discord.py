import os
import asyncio
import discord
import datetime
from tabulate import tabulate
from discord.ext import tasks, commands
import json
from dotenv import load_dotenv
from googletrans import Translator
from Word import Word, Paradigm, PREF_DEST
from wotd import word_of_the_day, WotdManager, FLAG, WORDCLASS, EXCL_LANG
from utilities import waittime_between

load_dotenv(dotenv_path='wotd_discord/.env')
TOKEN = os.getenv('DISCORD_TOKEN')
SAMIFLAG_ID = int(os.getenv('SAMIFLAG_ID'))
SPAM_CHANNEL_ID = int(os.getenv('SPAM_CHANNEL_ID'))
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


class WotdManagerDiscord(WotdManager):
    def __init__(self, d, path='wotd_discord/'):
        super().__init__(d, path)
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
            intro = f"<@&{self.role_id}>, dan biejjie baakoe lea **{word}**!\n Baakosne lea"
            intro = intro + \
                f"h {count} ulmieh:\n" if (
                    count > 1) else intro + f" akte ulmie:\n"
            return intro

    def get_translation(self, word, wordclass):
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
                main += f"\t{i}. {wordclass[m.pos]}\n"
                lastpos = m.pos
            main += trs_text
        return main, i

    def wotd_message(self, word):
        main, i = self.get_translation(word, self.wordclass)
        intro = self.get_intro_message(word, i)
        return intro + main


wotd_m = [WotdManagerDiscord(d) for d in ['smenob', 'smanob']]
bot = commands.Bot(command_prefix=']')
with open("language_conf.json", "r") as f:
    en_wc = json.load(f)["en"]["wordclass"]


@bot.command(name='paradigm', help="Shows the paradigm of a given word.")
async def paradigm(ctx, lang, word, pos=""):
    if ctx.channel.id != SPAM_CHANNEL_ID:
        await ctx.author.send(f"❌ You can only use that command in <#{SPAM_CHANNEL_ID}>.")
        return

    if not (lang in PREF_DEST):
        supported = "```sme\tNorthern Saami\nsma\tSouthern Saami\nsms\tSkolt Saami\nsmn\tInari Saami```"
        await ctx.send(f"<@{ctx.author.id}>, `{lang}` is not a supported language in paradigm search. Currently, the following languages are supported:\n{supported}")
        return

    ps = Paradigm(word, lang)
    if not ps.paradigms:
        await ctx.send(f"<@{ctx.author.id}>, no paradigm was found for `{word}` in the language `{lang}`. Are you sure that the word is spelled right?")
        return

    message = ""

    for p in ps.paradigms:
        if not p:
            continue
        wc = next(iter(p)).split("+")[0]  # Wordclass of paradigm element
        if pos:
            if wc == pos:
                table = [[k.replace("+", " "), i] for k, i in p.items()]
                message += f"```{tabulate(table, headers=['Word class.', 'Inflexion'])}```"
                break
            continue
        else:
            table = [[k.replace("+", " "), i] for k, i in p.items()]
            message += f"```{tabulate(table, headers=['Word class.', 'Inflexion'])}```"
            break

    if message:
        await ctx.send(f"<@{ctx.author.id}>, paradigm for **{word}**:\n{message}")
    else:
        await ctx.send(f"<@{ctx.author.id}>, I couldn't find any paradigm for `{word}` of the wordclass `{pos}`.")


@bot.command(name='word', help="Finds all possible translations for the given word and provides examples (if any).")
async def word(ctx, lang, word):
    if ctx.channel.id != SPAM_CHANNEL_ID:
        await ctx.author.send(f"❌ You can only use that command in <#{SPAM_CHANNEL_ID}>.")
        return

    if not (lang in ['sme', 'sma']):
        supported = "```sme\tNorthern Saami\nsma\tSouthern Saami```"
        await ctx.send(f"<@{ctx.author.id}>, `{lang}` is not a supported language for word search. Currently, the following languages are supported:\n{supported}")
        return

    try:
        w = Word(word, lang)
    except TypeError:
        await ctx.send(f"<@{ctx.author.id}>, no article was found `{word}` in the language `{lang}`. Are you sure that the word is spelled right (in the base form)?")
        return
    main = ""
    i = 0
    if lang == 'sme':
        main, i = wotd_m[0].get_translation(w, en_wc)
    elif lang == 'sma':
        main, i = wotd_m[1].get_translation(w, en_wc)
    intro = f"<@{ctx.author.id}>, the word **{word}** has {i} "
    intro = intro + "meanings:\n" if i > 1 else intro + "meaning:\n"
    await ctx.send(intro + main)


@tasks.loop(hours=24)
async def called_once_a_day():
    now = datetime.datetime.now()
    print(f"Fetching wotds for\t{now}")
    for m in wotd_m:
        word = m.get_wotd()
        print(f"{m.lang}-wotd: {word}", end="\t")
        wotd = m.wotd_message(word)
        message_channel = bot.get_channel(m.cha_id)
        await message_channel.send(wotd)
        print(f"Sent to {message_channel}!")
    print("Sleeping for 24h\n")


@called_once_a_day.before_loop
async def before():
    await bot.wait_until_ready()
    print(f'Finished waiting bot. {bot.user} has connected to Discord!')
    now = datetime.datetime.now()
    print(f"Time is currently \t{now}.")
    sleeptime = waittime_between(now, WOTD_H, WOTD_M, WOTD_S)
    print(
        f"WOTD is scheduled at \t{WOTD_H}H {WOTD_M}M {WOTD_S}S.")
    for w in wotd_m:
        print(w.lang, bot.get_channel(w.cha_id))
    print(f"Sleeptime: \t\t{datetime.timedelta(seconds=sleeptime)}")
    await asyncio.sleep(sleeptime)

called_once_a_day.start()
bot.run(TOKEN)
