from os import path
from PIL import Image
from time import mktime
from datetime import datetime
from discord import File, Embed
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
        supported = "```sme\tNorthern Saami\nsma\tSouthern Saami\nsms\tSkolt Saami\nsmn\tInari Saami\nnob\tNorwegian```"
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
    
    # Find another if the article is empty or an article about a date.
    if page["extract"] and not any(month in page["title"] for month in 
    ["Ođđajagimánu", "Guovvamánu", "Njukčamánu", "Cuoŋománu", 
    "Miessemánu", "Geassemánu", "Suoidnemánu", "Borgemánu", 
    "Čakčamánu", "Golggotmánu", "Skábmamánu", "Juovlamánu"]):
        return page["extract"]
    else:
        return await random_wiki_summary()

import feedparser
def parse_feed(url: str, cat: str = "") -> list:
    fd = feedparser.parse(url)
    entries = fd.entries
    if cat:
        valid_entries = []
        for e in entries:
            if "tags" in e:
                cats = [t.term for t in e.tags]
                if (cat in cats):
                    valid_entries.append(e)
            elif cat == "Ođđasat - Davvisámegillii":
                # If entry has no tags the article is sme.
                valid_entries.append(e)
        return valid_entries
    return entries

def filter_new_entries(entries: list, last_time: int) -> list:
    # GUIDs of the entries are always assumed to be sorted (high -> low = newest -> oldest)
    new_entries = []
    for e in entries:
        e_time = mktime(e.published_parsed)
        if e_time > last_time:
            new_entries.append(e)
        else:
            break
    return new_entries

def create_embed(entry, category: dict) -> Embed:
    # Creates an embed object that can be sent in discord
    try:
        timestamp = datetime.fromtimestamp(mktime(entry.published_parsed))
        embed = Embed(title=entry.title, url=entry.link, description=entry.summary, color=category["color"], timestamp=timestamp)
        
        embed.set_author(name=category["name"], url=category["url"], icon_url=category["icon_url"])
        #embed.set_thumbnail(url=category["thumbnail"])
        if "media_content" in entry:
            embed.set_image(url=entry.media_content[0]["url"])
        elif len(entry.links) > 1:
            for link in entry.links:
                if link["type"] == "image/jpeg":
                    # The thumbnails of Yle's newsfeed are found here
                    # Remove "//w_205,h_115,q_70" in url to find a higher res thumbnail
                    embed.set_image(url=link["href"].replace(r"//w_205,h_115,q_70", ""))
        # send with await ctx.send(embed=embed)
        return embed
    except Exception as err:
        print(err)
        exit(1)
    
    
def update_feed_and_create_embeds(last_time: int, category: dict):
    entries = parse_feed(category["rss"], cat=category["name"])
    new_entries = filter_new_entries(entries, last_time)
    embed_pairs = [(create_embed(e, category), int(mktime(e.published_parsed)) ) for e in new_entries]
    embed_pairs.reverse() # Reverse embeds in the order to be sent (oldest to newest)
    return embed_pairs
'''
oddasat = {
    "name": "Ođđasat - Davvisámegillii",
    "rss": "https://www.nrk.no/sapmi/oddasat.rss",
    "url": "https://www.nrk.no/sapmi/davvisamegillii/",
    "icon_url": "https://gfx.nrk.no/1IC-Q4_HFRVuBYc842UQJwEH-mCfzezjzziUZClFOf-g"
}

entries = parse_feed("https://www.nrk.no/sapmi/oddasat.rss")
new_entries = filter_new_entries(entries, 15563162)
print(new_entries[5])
'''