from os import path
from PIL import Image
from discord import File
from textgenrnn import textgenrnn
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import numpy as np
import matplotlib.pyplot as plt
import os


def reindeer_wc(text):
    # get data directory (using getcwd() is needed to support running example in generated IPython notebook)
    d = path.dirname(__file__)

    # read the mask image
    reindeer_mask = np.array(Image.open(path.join(d, "reindeer.png")))

    stopwords = set(STOPWORDS)
    with open(path.join(d, "wc_ignore.txt"), "r", encoding="utf-8") as f:
        for w in f.read().split('\n'):
            stopwords.add(w)

    wc = WordCloud(background_color="black", max_words=3000, mask=reindeer_mask,
                   stopwords=stopwords)

    # create coloring from image
    im_colors = ImageColorGenerator(reindeer_mask)

    # generate word cloud
    wc.generate(text)
    
    wc.recolor(color_func=im_colors)

    # store to file
    wc.to_file(path.join(d, "final_wc.png"))

    wc_file = File(path.join(d, "final_wc.png"), "wordcloud.png")
    return wc_file

def imitation(text):
    rnn = textgenrnn()
    rnn.train_on_texts([text], num_epochs=3)
    imit = str(rnn.generate(return_as_list=True)[0])
    return imit