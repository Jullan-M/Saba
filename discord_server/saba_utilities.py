from os import path
from PIL import Image
from discord import File
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import asyncio
import numpy as np
import matplotlib.pyplot as plt
import os
import requests


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


def is_mentioned(user_id, msg):
    return (msg.guild.get_member(user_id) in msg.mentions)


async def correct_channel(ctx, spam_cha):
    if ctx.channel.id != spam_cha:
        await ctx.author.send(f"❌ You can only use that command in <#{spam_cha}>.")
        return False
    return True


async def supported_lang(ctx, lang, pref_dest):
    if not (lang in pref_dest):
        supported = "```sme\tNorthern Saami\nsma\tSouthern Saami\nsms\tSkolt Saami\nsmn\tInari Saami```"
        await ctx.send(f"<@{ctx.author.id}>, `{lang}` is not a supported language for this command. Currently, the following languages are supported:\n{supported}")
        return False
    return True


async def reindeer_wc(text):
    # get data directory (using getcwd() is needed to support running example in generated IPython notebook)
    d = path.dirname(__file__)

    # read the mask image
    reindeer_mask = np.array(Image.open(path.join(d, "reindeer.png")))

    stopwords = set(STOPWORDS)
    with open(path.join(d, "wc_ignore.txt"), "r", encoding="utf-8") as f:
        for w in f.read().split('\n'):
            stopwords.add(w)

    wc = WordCloud(background_color=None, mode="RGBA", max_words=3000, mask=reindeer_mask,
                   stopwords=stopwords, collocations=False)

    # create coloring from image
    im_colors = ImageColorGenerator(reindeer_mask)

    # generate word cloud
    wc.generate(text)

    wc.recolor(color_func=im_colors)

    # store to file
    wc.to_file(path.join(d, "final_wc.png"))

    wc_file = File(path.join(d, "final_wc.png"), "wordcloud.png")
    return wc_file

async def random_wiki_summary():
    r = requests.get("https://se.wikipedia.org/wiki/Erenoam%C3%A1%C5%A1:Summal")
    r = requests.get(f"https://se.wikipedia.org/api/rest_v1/page/summary/{r.url.split('/')[-1]}")
    page = r.json()
    
    if page["extract"]:
        return page["extract"]
    else:
        return await random_wiki_summary()