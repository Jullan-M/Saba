import os
import time
import datetime

from twython import Twython
from dotenv import load_dotenv
from googletrans import Translator
from wotd import word_of_the_day, FLAG, WORDCLASS, EXCL_LANG
from utilities import waittime_between
from imutils import examples_img

load_dotenv()
APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')
OAUTH_TOKEN = os.getenv('OAUTH_TOKEN')
OAUTH_TOKEN_SECRET = os.getenv('OAUTH_TOKEN_SECRET')

WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))


def wotd_message(word):
    trns = Translator()
    main = ""
    lastpos = ""
    lastword = ""
    lastdesc = ""
    examples = ["", "", ""]
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
                trs_text += f" {FLAG[tr.lang]} {tr} {tr.desc}  →  {FLAG['en']} {tr_en} {desc_en}\n"
                for ex in tr.examples:
                    ex_en = trns.translate(ex[1], src='no', dest='en').text
                    examples[0] += f"– {ex[0]}\n"
                    examples[1] += f"– {ex[1]}\n"
                    examples[2] += f"– {ex_en}\n"
            else:
                trs_text += f" {FLAG[tr.lang]} {tr}\n"
        if lastpos != m.pos and trs_text:
            i += 1
            main += f"{i}. {WORDCLASS[m.pos]}\n"
            lastpos = m.pos
        main += trs_text

    if examples[0]:
        for n, ex in enumerate(examples):
            if ex[-1] == "\n":
                examples[n] = ex[:-1]

    intro = f"Otná sátni lea {word}!\nSánis lea"
    intro = intro + \
        f"t {i} mearkkašumit:\n" if (
            i > 1) else intro + f" okta mearkkašupmi:\n"

    return intro + main, examples_img(str(word), examples)


def run_twitter_bot(d):
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    now = datetime.datetime.now()
    print(f"Time is currently \t{now}.")
    sleeptime = waittime_between(now, WOTD_H, WOTD_M - 1, WOTD_S)
    print(
        f"{d}-WOTD is scheduled at \t{WOTD_H}H {WOTD_M}M {WOTD_S}S.")
    print(f"Sleeptime: \t\t{datetime.timedelta(seconds=sleeptime)}")
    time.sleep(sleeptime)

    while True:
        word = word_of_the_day(d)
        print("Today's word is:", word)
        print("Generating message...")
        wotd, incExample = wotd_message(word)
        now = datetime.datetime.now()
        print(f"Finished generating message at {now}")
        sleeptime = waittime_between(now, WOTD_H, WOTD_M, WOTD_S)
        print(f"sleeping for {sleeptime}s...")
        time.sleep(sleeptime)
        if incExample:
            example_file = open('media/examples.png', 'rb')
            response = twitter.upload_media(media=example_file)
            twitter.update_status(status=wotd, media_ids=[
                                  response['media_id']])
            print(f"WOTD was sent to Twitter with example.\n")
        else:
            twitter.update_status(status=wotd)
            print(f"WOTD was sent to Twitter.\n")

        now = datetime.datetime.now()
        time.sleep(waittime_between(now, WOTD_H, WOTD_M, WOTD_S))


run_twitter_bot('smenob')
