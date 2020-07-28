import os
import asyncio
import discord
import datetime
import random
from tabulate import tabulate
from discord.ext import tasks, commands
import json
from dotenv import load_dotenv
from googletrans import Translator
from Word import Word, Paradigm, Inflection, PREF_DEST
from wotd import word_of_the_day, check_special_wotd, WotdManager, FLAG
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

    def get_intro_message(self, word, count, spec=""):
        intro = spec.replace("<WORD>", f"**{word}**")
        if self.lang == 'sme':
            if not intro:
                intro = f"<@&{self.role_id}>, otná sátni lea **{word}**!"
            else:
                intro = f"<@&{self.role_id}> " + intro
            intro += "\nSánis lea"
            intro = intro + \
                f"t {count} mearkkašumit:\n" if (
                    count > 1) else intro + f" okta mearkkašupmi:\n"
            return intro

        elif self.lang == 'sma':
            if not intro:
                intro = f"<@&{self.role_id}>, daen biejjien baakoe lea **{word}**!"
            else:
                intro = f"<@&{self.role_id}> " + intro
            intro += "\nBaakoen lea"
            intro = intro + \
                f"h {count} goerkesimmieh:\n" if (
                    count > 1) else intro + f" akte goerkesimmie:\n"
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
                    tr_en = ""
                    if m.pos != "V":
                        tr_en = ", ".join([w.text for w in trns.translate(
                            str(tr).split(", "), src='no', dest='en')])
                    else:
                        # Add "å" prefix to verbs in order to enhance translation
                        tr_en = ", ".join([w.text[3:] for w in trns.translate(
                            ["å " + v for v in str(tr).split(", ")], src='no', dest='en')])
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
                elif tr.lang == 'swe':
                    if "_SWE" in str(tr):
                        # This is a workaround for the {NOR word}_SWE word bug in sma dictionaries
                        fixed_tr = trns.translate(str(tr).replace(
                            "_SWE", ""), src='no', dest='sv').text
                        trs_text += f"\t\t{FLAG[tr.lang]} {fixed_tr}\n"
                else:
                    trs_text += f"\t\t{FLAG[tr.lang]} {tr}\n"
                    trs_text = trs_text.replace(
                        "<SFLAG>", f"<:samiflag:{SAMIFLAG_ID}>")
            if lastpos != m.pos and trs_text:
                i += 1
                main += f"\t{i}. {wordclass[m.pos]}\n"
                lastpos = m.pos
            main += trs_text
        return main, i

    def wotd_message(self, word, spec=""):
        main, i = self.get_translation(word, self.wordclass)

        intro = self.get_intro_message(word, i, spec=spec)
        return intro + main


wotd_m = [WotdManagerDiscord(d) for d in ['smenob', 'smanob']]
bot = commands.Bot(command_prefix=commands.when_mentioned_or(']'))
with open("language_conf.json", "r") as f:
    en_wc = json.load(f)["en"]["wordclass"]
with open("wotd_discord/bot_responses.json", "r", encoding="utf-8") as f:
    botres = json.load(f)

async def correct_channel(ctx):
    if ctx.channel.id != SPAM_CHANNEL_ID:
        await ctx.author.send(f"❌ You can only use that command in <#{SPAM_CHANNEL_ID}>.")
        return False
    return True

async def supported_lang(ctx, lang):
    if not (lang in PREF_DEST):
        supported = "```sme\tNorthern Saami\nsma\tSouthern Saami\nsms\tSkolt Saami\nsmn\tInari Saami```"
        await ctx.send(f"<@{ctx.author.id}>, `{lang}` is not a supported language for this command. Currently, the following languages are supported:\n{supported}")
        return False
    return True


@bot.command(name='examine', help="Shows recursively the morphological tags and lemma for a given word. Explanation for the tags can be found here: https://giellalt.uit.no/lang/sme/docu-mini-smi-grammartags.html")
async def examine(ctx, lang: str, word: str):
    if not await correct_channel(ctx): return
    
    if not await supported_lang(ctx, lang): return

    inf = Inflection(word, lang)
    if not inf.inflections:
        await ctx.send(f"<@{ctx.author.id}>, no details were found for `{word}` in the language `{lang}`. Are you sure that the word is spelled right?")
        return
    
    message = f"```{tabulate(inf.inflections, headers=['Lemma', 'Morph. Tags'])}```"
    await ctx.send(f"<@{ctx.author.id}>, morphological analysis for the word **{word}**:\n{message}")



@bot.command(name='paradigm', help="Shows the paradigm of a given word.")
async def paradigm(ctx, lang: str, word: str, pos=""):
    if not await correct_channel(ctx): return
    
    if not await supported_lang(ctx, lang): return

    ps = Paradigm(word, lang)
    if not ps.paradigms:
        await ctx.send(f"<@{ctx.author.id}>, no paradigm was found for `{word}` in the language `{lang}`. Are you sure that the word is spelled right?")
        return

    message = ""

    for p in ps.paradigms:
        if not p:
            continue
        wc = next(iter(p)).split("+")[0]  # Wordclass of paradigm element
        # Numbering (Sg, Du, Pl), only used for pronouns
        num = next(iter(p)).split("+")[2] if wc == "Pron" else ""
        table = [[k.replace("+", " "), i] for k, i in p.items()]
        if pos:
            if wc == pos:
                if pos != "Pron":
                    message += f"```{tabulate(table, headers=['Word class.', 'Inflexion'])}```"
                    break
                else:
                    message += f"*Pronoun ({num})*\n```{tabulate(table, headers=['Word class.', 'Inflexion'])}```"
        else:
            if wc != "Pron":
                message += f"```{tabulate(table, headers=['Word class.', 'Inflexion'])}```"
                break
            else:
                message += f"*Pronoun ({num})*\n```{tabulate(table, headers=['Word class.', 'Inflexion'])}```"

    if message:
        await ctx.send(f"<@{ctx.author.id}>, paradigm for **{word}**:\n{message}")
    else:
        end = f" in the wordclass {pos}." if pos else "."
        await ctx.send(f"<@{ctx.author.id}>, I couldn't find any paradigm for `{word}`{end}")


@bot.command(name='word', help="Finds all possible translations for the given word and provides examples (if any).")
async def word(ctx, lang: str, word: str):
    if not await correct_channel(ctx): return

    if not (lang in ['sme', 'sma']):
        supported = "```sme\tNorthern Saami\nsma\tSouthern Saami```"
        await ctx.send(f"<@{ctx.author.id}>, `{lang}` is not a supported language for word search. Currently, the following languages are supported:\n{supported}")
        return

    try:
        w = Word(word, lang)
    except TypeError:
        await ctx.send(f"<@{ctx.author.id}>, no article was found for `{word}` in the language `{lang}`. Are you sure that the word is spelled right (in the base form)?")
        return
    main = ""
    i = 0
    if lang == 'sme':
        main, i = wotd_m[0].get_translation(w, en_wc)
    elif lang == 'sma':
        main, i = wotd_m[1].get_translation(w, en_wc)
    intro = f"<@{ctx.author.id}>, **{word}** has {i} "
    intro = intro + "meanings:\n" if i > 1 else intro + "meaning:\n"
    await ctx.send(intro + main)


@bot.command(name='sátni', help="An alias for ]word sme <word> (look-up in Northern Sami dictionaries).")
async def satni(ctx, word: str):
    await word(ctx, 'sme', word)


@bot.command(name='baakoe', help="An alias for ]word sma <word> (look-up in Southern Sami dictionaries).")
async def baakoe(ctx, word: str):
    await word(ctx, 'sma', word)
'''
@bot.command(name='báhko', help="Lule-Sami to Norwegian dictionary look-up.")
async def bahko(ctx, word: str):
    if not await correct_channel(ctx): return

    rslts = []
    with open("smjnob_words.txt", "r") as f:
        for line in f:
            for w in line.split(" "):
                if word in line:
                    rslts.append(line)
    
    if len(rslts):
        await ctx.send(f"No result were found for {word}. Are you sure the word is spelled right")
'''



@bot.event
async def on_message(msg):
    await bot.process_commands(msg)

    if msg.content[0] == bot.command_prefix:
        return
    
    if len(msg.content) > 200:
        return

    if msg.author == bot.user:
        return
    
    message = msg.content.lower()
    now = datetime.datetime.now().time()
    for call in botres:
        if call in message:
            from_hr = datetime.time(botres[call]["int"][0])
            to_hr = datetime.time(botres[call]["int"][1])
            diff = to_hr.hour - from_hr.hour

            if ( (diff > 0 and (now >= from_hr and now < to_hr)) or 
            (diff < 0 and (now >= from_hr or now < to_hr)) or 
            diff == 0):
                await msg.channel.send(random.choice(botres[call]["res"]))
                return
    



@tasks.loop(hours=24)
async def called_once_a_day():
    now = datetime.datetime.now()
    print(f"Fetching wotds for\t{now}")
    for m in wotd_m:
        wotd = ""
        spec_day = check_special_wotd(now.strftime("%d%m"), m.lang)
        pic = False

        if spec_day:
            spec_word = random.choice(spec_day["w"])
            pic = spec_day["pic"]
            wotd = m.wotd_message(
                Word(spec_word, m.lang), spec=spec_day["intro"])
            print(f"{m.lang}-wotd (SPECIAL): {spec_word}", end="\t")
        else:
            word = m.get_wotd()
            print(f"{m.lang}-wotd: {word}", end="\t")
            wotd = m.wotd_message(word)

        if pic:
            pass
            print(f"Sent to {message_channel} with pic!")
        else:
            message_channel = bot.get_channel(m.cha_id)
            await message_channel.send(wotd)
            print(f"Sent to {message_channel}!")
    print("Sleeping for 24h\n")


@called_once_a_day.before_loop
async def before():
    await bot.wait_until_ready()
    await bot.change_presence(activity=discord.Game(name=f"with {random.choice(['nouns. 🖊️', 'verbs. ✎', 'adjectives. 🖋️', 'possessive suffixes. ✍️', 'Finno-Ugric languages. 📝'])}"))
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
