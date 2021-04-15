import os
import asyncio
import datetime
import random
import json
import discord
import typing
import re
from tabulate import tabulate
from discord.ext import tasks, commands
from discord_server import saba_utilities as sbut
from dotenv import load_dotenv
from googletrans import Translator
from Word import Word, Paradigm, Inflection, PREF_DEST
from wotd import word_of_the_day, check_special_wotd, WotdManager, FLAG
from utilities import waittime_between, TW_COLORS

load_dotenv(dotenv_path='discord_server/.env')
TOKEN = os.getenv('DISCORD_TOKEN')
SAMIFLAG_ID = int(os.getenv('SAMIFLAG_ID'))
SPAM_CHANNEL_ID = int(os.getenv('SPAM_CHANNEL_ID'))
WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))


class WotdManagerDiscord(WotdManager):
    def __init__(self, d, path='discord_server/'):
        super().__init__(d, path)
        cha = os.getenv(f'{self.lang.upper()}_CHANNEL_ID')
        rol = os.getenv(f'{self.lang.upper()}_ROLE_ID')
        self.cha_id = int(cha) if cha else 0
        self.role_id = int(rol) if rol else 0

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

    async def get_translation(self, word, wordclass):
        try:
            trns = Translator(service_urls=['translate.googleapis.com'])
            main = ""
            lastpos = ""
            lastword = ""
            lastdesc = ""
            i = 0
            for m in word.meanings:
                trs_text = ""
                for tr in m.trs:
                    if (lastword == str(tr) and lastdesc == tr.desc):
                        continue
                    lastword = str(tr)
                    lastdesc = tr.desc

                    if tr.lang == 'nob' or tr.lang == 'fin' or tr.lang == 'fi':
                        tr_en = ""
                        if m.pos == "V" and tr.lang == 'nob':
                            # Add "å" prefix to verbs in order to enhance translation
                            tr_en = ", ".join([w.text.replace("to ", "") for w in trns.translate(
                                ["å " + v for v in str(tr).split(", ")], src='no', dest='en')])
                        else:
                            tr_en = ", ".join([w.text for w in trns.translate(
                                str(tr).split(", "), src=tr.lang[:2], dest='en')])
                        desc_en = trns.translate(
                            tr.desc, src=tr.lang[:2], dest='en').text if tr.desc else ''
                        trs_text += f"\t\t{FLAG[tr.lang]} {tr} {tr.desc}\t→\t{FLAG['en']} {tr_en} {desc_en}\n"
                        for n, ex in enumerate(tr.examples):
                            ex_en = trns.translate(
                                ex[1], src=tr.lang[:2], dest='en').text
                            trs_text += f"> <:samiflag:{SAMIFLAG_ID}> *{sbut.underscore_word(ex[0], str(word))}*\n"
                            trs_text += f"> {FLAG[tr.lang]} *{sbut.underscore_word(ex[1], str(tr))}*\n"
                            trs_text += f"> {FLAG['en']} *{sbut.underscore_word(ex_en, tr_en)}*\n"
                            if (n != len(tr.examples)-1):
                                trs_text += "\n"
                    else:
                        trs_text += f"\t\t{FLAG[tr.lang]} {tr} {tr.desc}\n"
                        trs_text = trs_text.replace(
                            "<SFLAG>", f"<:samiflag:{SAMIFLAG_ID}>")
                if lastpos != m.pos and trs_text:
                    i += 1
                    main += f"\t{i}. {wordclass[m.pos]}\n"
                    lastpos = m.pos
                main += trs_text
            return main, i
        except AttributeError:
            print("AttributeError. Trying again in 0.1 seconds...")
            await asyncio.sleep(0.1)
            return await self.get_translation(word, wordclass)

    async def wotd_message(self, word, spec=""):
        main, i = await self.get_translation(word, self.wordclass)

        intro = self.get_intro_message(word, i, spec=spec)
        return intro + main


wotd_m = [WotdManagerDiscord(d) for d in ['smenob', 'smanob']]
wotd_nob = WotdManagerDiscord('nobsme')
bot = commands.Bot(command_prefix=commands.when_mentioned_or(']'))

with open("language_conf.json", "r") as f:
    en_wc = json.load(f)["en"]["wordclass"]
with open("discord_server/bot_responses.json", "r", encoding="utf-8") as f:
    botres = json.load(f)

last_mention = datetime.datetime.now()
last_response = ""


@bot.command(name='examine', help="Shows recursively the morphological tags and lemma for a given word. Explanation for the tags can be found here: https://giellalt.uit.no/lang/sme/docu-mini-smi-grammartags.html")
async def examine(ctx, lang: str, word: str):
    if not await sbut.correct_channel(ctx, SPAM_CHANNEL_ID):
        return

    if not await sbut.supported_lang(ctx, lang, PREF_DEST):
        return

    inf = Inflection(word, lang)
    if not inf.inflections:
        await ctx.send(f"<@{ctx.author.id}>, no details were found for `{word}` in the language `{lang}`. Are you sure that the word is spelled right?")
        return

    message = f"```{tabulate(inf.inflections, headers=['Lemma', 'Morph. Tags'])}```"
    await ctx.send(f"<@{ctx.author.id}>, morphological analysis for the word **{word}**:\n{message}")


@bot.command(name='paradigm', help="Shows the paradigm of a given word.")
async def paradigm(ctx, lang: str, word: str, pos=""):
    if not await sbut.correct_channel(ctx, SPAM_CHANNEL_ID):
        return

    if not await sbut.supported_lang(ctx, lang, PREF_DEST):
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


@bot.command(name='báhko', help="Lule-Sami to Norwegian dictionary look-up.")
async def bahko(ctx, word: str):
    if not await sbut.correct_channel(ctx, SPAM_CHANNEL_ID):
        return

    rslts = []
    extra = []
    with open("smjnob_words.txt", "r", encoding="utf-8") as f:
        for line in f:
            entry = line.replace("\n", "")
            if entry == word:
                rslts.append(entry)
                break
        if not rslts:
            f.seek(0)
            for line in f:
                entry = line.replace("\n", "")
                for w in entry.split(" "):
                    if w == word:
                        rslts.append(entry)
    if rslts:
        if len(rslts) == 1:
            with open("smjnob_dict.json", "r", encoding="utf-8") as f:
                transl = json.load(f)[rslts[0]]
            intro = f"<@{ctx.author.id}>, Lule-Sami dictionary entry for **{rslts[0]}**:"
            main = f"```fix\n{transl}```"
            await ctx.send(intro + main)
        else:
            intro = f"<@{ctx.author.id}>, the following was found in the Lule-Sami dictionary (please specify with qoutation marks):"
            main = "```" + '\n'.join(rslts) + "```"
            await ctx.send(intro + main)
    else:
        await ctx.send(f"<@{ctx.author.id}>, no dictonary entries were found.")


@bot.command(name='word', help="Finds all possible translations for the given word and provides examples (if any).")
async def word(ctx, lang: str, word: str):
    if not await sbut.correct_channel(ctx, SPAM_CHANNEL_ID):
        return

    if not (lang in ['sme', 'sma', 'nob']):
        supported = "```sme\tNorthern Saami\nsma\tSouthern Saami\nnob\tNorwegian (bokmål)```"
        await ctx.send(f"<@{ctx.author.id}>, `{lang}` is not a supported language for word search. Currently, the following languages are supported:\n{supported}")
        return

    w = Word(word, lang)

    if not w.meanings:
        await ctx.send(f"<@{ctx.author.id}>, no article was found for `{word}` in the language `{lang}`. Are you sure that the word is spelled right (in the base form)?")
        return

    main = ""
    i = 0
    if lang == 'sme':
        main, i = await wotd_m[0].get_translation(w, en_wc)
    elif lang == 'sma':
        main, i = await wotd_m[1].get_translation(w, en_wc)
    elif lang == 'nob':
        main, i = await wotd_nob.get_translation(w, en_wc)
    elif lang == 'smj':
        return await bahko(ctx, word)

    intro = f"{ctx.author.mention}, **{word}** (`{lang}`) has {i} "
    intro = intro + "meanings:\n" if i > 1 else intro + "meaning:\n"
    try:
        await ctx.send(intro + main)
    except Exception as err:
        err_msg = await ctx.send(f"I encountered the following error:\n{err}")
        await asyncio.sleep(60)
        await err_msg.delete()


@bot.command(name='sátni', help="An alias for ]word sme <word> (look-up in Northern Sami dictionaries).")
async def satni(ctx, term: str):
    await word(ctx, 'sme', term)


@bot.command(name='baakoe', help="An alias for ]word sma <word> (look-up in Southern Sami dictionaries).")
async def baakoe(ctx, term: str):
    await word(ctx, 'sma', term)


@bot.command(name='ord', help="An alias for ]word nob <word> (look-up in Norwegian (bokmål) - Sami dictionaries).")
async def ords(ctx, term: str):
    await word(ctx, 'nob', term)


async def sample_messages(ctx, source: typing.Union[discord.TextChannel, discord.Member, int], location: typing.Union[discord.TextChannel, int]):
    ignore_words = ["]paradigm", "]sátni", "]baakoe", "]báhko",
                    "]word", "]examine", "]help", "]imitate", "!play", "!skip", "!p", ".stats"]
    ignore_bots = [302050872383242240, 159985870458322944,
                   550613223733329920, 724693719013392456]

    start = await ctx.send("Beginning to sample messages...")
    cnt_msg = await ctx.send("`0 messages sampled`")
    sample = ""
    count = 0

    async def ignorable(message, ignores):
        for excl in ignores:
            if (excl in message):
                return True
        return False

    async def all_messages(cha_history):
        nonlocal sample
        nonlocal count
        async for msg in cha_history:
            if (msg.content and not (msg.author.id in ignore_bots)):
                if await ignorable(msg.content, ignore_words):
                    continue
                sample = sample + msg.content + "\n"
                count += 1
                if count % 100 == 0:
                    await cnt_msg.edit(content=f"`{count} messages sampled`")

    async def user_messages(cha_history):
        nonlocal sample
        nonlocal count
        async for msg in cha_history:
            if (msg.content and msg.author.id == source.id):
                if await ignorable(msg.content, ignore_words):
                    continue
                sample = sample + msg.content + "\n"
                count += 1
                if count % 100 == 0:
                    await cnt_msg.edit(content=f"`{count} messages sampled`")

    async def channel_messages(cha_history):
        nonlocal sample
        nonlocal count
        async for msg in cha_history:
            if (msg.content and not (msg.author.id in ignore_bots)):
                if await ignorable(msg.content, ignore_words):
                    continue
                sample = sample + msg.content + "\n"
                count += 1
                if count % 100 == 0:
                    await cnt_msg.edit(content=f"`{count} messages sampled`")

    async def user_cha_messages(cha_history):
        nonlocal sample
        nonlocal count
        async for msg in cha_history:
            if (msg.content and msg.author.id == source.id):
                if await ignorable(msg.content, ignore_words):
                    continue
                sample = sample + msg.content + "\n"
                count += 1
                if count % 100 == 0:
                    await cnt_msg.edit(content=f"`{count} messages sampled`")

    async def fetch_messages(case_func, channel):
        try:
            await case_func(channel.history(oldest_first=False, limit=7500))
        except discord.Forbidden:
            print(f"Could not access channel #{channel}. Skipping.")

    server = ctx.guild

    if type(source) == discord.TextChannel:
        if source.permissions_for(server.get_member(bot.user.id)).read_messages:
            await start.edit(content=f"Sampling all messages in {source.mention}...")
            await fetch_messages(channel_messages, source)
        else:
            await start.edit(content=f"I don't have the permissions to read messages in that channel.")
            return ""
    elif type(source) == discord.Member and type(location) == discord.TextChannel:
        if location.permissions_for(server.get_member(bot.user.id)).read_messages:
            await start.edit(content=f"Sampling {source}'s messages in {location.mention}...")
            await fetch_messages(user_cha_messages, location)
        else:
            await start.edit(content=f"I don't have the permissions to read messages in that channel.")
            return ""
    elif type(source) == discord.Member:
        for channel in server.text_channels:
            await start.edit(content=f"Sampling {source}'s messages in {server.name} discord server...")
            await fetch_messages(user_messages, channel)
    elif type(source) == int:
        for channel in server.text_channels:
            await start.edit(content=f"Sampling all messages of {server.name} discord server...")
            await fetch_messages(all_messages, channel)
    else:
        await start.edit(content=f"Invalid command arguments. Use `@`/`#` to mention user/channel.")
        return ""
    await cnt_msg.delete()
    await start.delete()
    sample = re.sub('<[^>]+>', '', sample)
    return sample, count


@bot.command(name='wordcloud', help="Generates a word cloud for a given user or channel in the server. <source>: user/channel (everyone and every channel if not specified), <location>: channel (every channel if not specified)")
async def wordcloud(ctx, source: typing.Union[discord.TextChannel, discord.Member, int] = 0, location: typing.Union[discord.TextChannel, int] = 0):
    sample, count = await sample_messages(ctx, source, location)
    if sample:
        wc_file = await sbut.reindeer_wc(sample)
        context = ""
        if type(source) == discord.TextChannel:
            context = f"{ctx.author.mention}, word cloud of {source.mention} (`{count}` messages sampled):"
        elif type(source) == discord.Member and type(location) == discord.TextChannel:
            context = f"{ctx.author.mention}, word cloud of {source}'s messages in {location.mention} (`{count}` messages sampled):"
        elif type(source) == discord.Member:
            context = f"{ctx.author.mention}, word cloud of {source}'s messages (`{count}` messages sampled):"
        else:
            context = f"{ctx.author.mention}, word cloud of {ctx.guild} discord server (`{count}` messages sampled):"
        await ctx.send(context, file=wc_file)
    else:
        return


@bot.command(name='imitate', help="Imitates a user/channel with machine learning. <source>: user/channel (everyone and every channel if not specified), <location>: channel (every channel if not specified)")
async def imitate(ctx, source: typing.Union[discord.TextChannel, discord.Member, int] = 0, location: typing.Union[discord.TextChannel, int] = 0):

    await ctx.send(f"{ctx.author.mention}, this function is unavailabe right now – no GPU was found on the host machine.")
    return
    '''

    sample = await sample_messages(ctx, source, location)
    if sample:
        train = await ctx.send("Training neural networks with samples...")
        imits = await sbut.imitation(sample)
        await train.delete()
        context = ""
        if type(source) == discord.TextChannel:
            context = f"{ctx.author.mention}, imitation of messages in {source.mention}:\n> "
        elif type(source) == discord.Member and type(location) == discord.TextChannel:
            context = f"{ctx.author.mention}, imitation of {source}'s messages in {location.mention}:\n> "
        elif type(source) == discord.Member:
            context = f"{ctx.author.mention}, imitation of {source}:\n> "
        else:
            context = f"{ctx.author.mention}, imitation of {ctx.guild}:\n> "
        await ctx.send(context + "\n\n> ".join(imits))
    else:
        await ctx.send(f"No messages found from user in channel/server.")
        return
    '''


@bot.command(name='del_msg', help="Dev command")
async def del_msg(ctx, cha_id, msg_id):
    if int(ctx.author.id) != 252228069434195968:
        return

    await bot.http.delete_message(cha_id, msg_id)


@bot.command(name='force_wotd', help="Dev command")
async def force_wotd(ctx, lang):
    if int(ctx.author.id) != 252228069434195968:
        return
    lang_val = {"sme": 0, "sma": 1}
    i = lang_val[lang]
    if not lang in lang_val:
        return

    wotd = ""
    spec_day = check_special_wotd(
        datetime.datetime.now().strftime("%d%m"), wotd_m[i].lang)
    pic = False

    if spec_day:
        spec_word = random.choice(spec_day["w"])
        pic = spec_day["pic"]
        wotd = await wotd_m[i].wotd_message(
            Word(spec_word, wotd_m[i].lang), spec=spec_day["intro"] if "intro" in spec_day else "")
        print(f"FORCED {wotd_m[i].lang}-wotd (SPECIAL): {spec_word}", end="\t")
    else:
        word = wotd_m[i].get_wotd()
        print(f"FORCED {wotd_m[i].lang}-wotd: {word}", end="\t")
        wotd = await wotd_m[i].wotd_message(word)

    message_channel = bot.get_channel(wotd_m[i].cha_id)
    if pic:
        pass
        print(f"Sent to {message_channel} with pic!")
    else:
        await message_channel.send(wotd)
        print(f"Sent to {message_channel}!")


@bot.event
async def on_message(msg):
    global last_mention
    global last_response
    await bot.process_commands(msg)

    if (not msg.content or msg.content[0] == bot.command_prefix or
            len(msg.content) > 200 or msg.author == bot.user):
        return

    message = msg.content.lower()
    now = datetime.datetime.now()
    for call in botres["canned"]:
        if call in message:
            from_hr = datetime.time(botres["canned"][call]["int"][0])
            to_hr = datetime.time(botres["canned"][call]["int"][1])
            diff = to_hr.hour - from_hr.hour
            now_hr = now.time()

            if ((diff > 0 and (now_hr >= from_hr and now_hr < to_hr)) or
                    (diff < 0 and (now_hr >= from_hr or now_hr < to_hr)) or
                    diff == 0):
                await msg.channel.send(random.choice(botres["canned"][call]["res"]).replace("<author>", msg.author.mention))
                return

    if (("Saba" in msg.content) or sbut.is_mentioned(bot.user.id, msg)):
        if (now - last_mention).total_seconds() > 5400:
            last_mention = datetime.datetime.now()
            if random.random() > 0.8:
                response = random.choice(botres["mention"])
                while response["res"] == last_response:
                    response = random.choice(botres["mention"])

                last_response = response["res"]
                if response["file"]:
                    file = discord.File(f"media/{response['file']}")
                    await msg.channel.send(response["res"].replace("<author>", msg.author.mention), file=file)
                else:
                    await msg.channel.send(response["res"].replace("<author>", msg.author.mention))
            else:
                summary = await sbut.random_wiki_summary()
                intro = random.choice(["Dihtetgo don <author> ahte ", "<author>, leatgo goassege gullan ahte ", "Leango mun goassege muitalan dutnje, <author>, ahte ", "<author>, dongal berret diehtit ahte ", "Leago dutnje goassege časkán jurdagii ahte "])
                await msg.channel.send(intro.replace("<author>", msg.author.mention) + summary)
        else:
            await msg.add_reaction(random.choice(botres["reactions"]))


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
            wotd = await m.wotd_message(
                Word(spec_word, m.lang), spec=spec_day["intro"] if "intro" in spec_day else "")
            print(f"{m.lang}-wotd (SPECIAL): {spec_word}", end="\t")
        else:
            word = m.get_wotd()
            print(f"{m.lang}-wotd: {word}", end="\t")
            wotd = await m.wotd_message(word)

        message_channel = bot.get_channel(m.cha_id)
        if pic:
            pass
            print(f"Sent to {message_channel} with pic!")
        else:
            await message_channel.send(wotd)
            print(f"Sent to {message_channel}!")
    print("Sleeping for 24h\n")


@called_once_a_day.before_loop
async def before():
    await bot.wait_until_ready()
    await bot.change_presence(activity=discord.Game(name=f"{random.choice(['with nouns. 🖊️', 'with verbs. ✎', 'with adjectives. 🖋️', 'with possessive suffixes. ✍️', 'with Finno-Ugric languages. 📝', 'with the fate of those on The List.', 'Daabloe ♟️', 'Sáhkku ♙', 'Tablut 🎲'])}"))
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
