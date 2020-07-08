import os
import time
import datetime

from twython import Twython
from dotenv import load_dotenv
from googletrans import Translator
from wotd import word_of_the_day, WotdManager, FLAG, WORDCLASS, EXCL_LANG
from Word import Word
from utilities import waittime_between
from imutils import examples_img

load_dotenv(dotenv_path='wotd_twitter/.env')
APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')
OAUTH_TOKEN = os.getenv('OAUTH_TOKEN')
OAUTH_TOKEN_SECRET = os.getenv('OAUTH_TOKEN_SECRET')

WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))


class WotdManagerTwitter(WotdManager):
    def __init__(self, d, path='wotd_twitter/'):
        super().__init__(d, path)
        self.excl_lang.append("smn")

    def get_intro_message(self, word, count):
        if self.lang == 'sme':
            intro = f"Otná sátni lea {word}!\nSánis lea"
            intro = intro + \
                f"t {count} mearkkašumit:\n" if (
                    count > 1) else intro + f" okta mearkkašupmi:\n"
            return intro

        elif self.lang == 'sma':
            intro = f"Dan biejjie baakoe lea {word}!\nSánis lea"
            intro = intro + \
                f"t {count} mearkkašumit:\n" if (
                    count > 1) else intro + f" okta mearkkašupmi:\n"
            return intro

    def wotd_message(self, word):
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
                if tr.lang in self.excl_lang or (lastword == str(tr) and lastdesc == tr.desc):
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
                main += f"{i}. {self.wordclass[m.pos]}\n"
                lastpos = m.pos
            main += trs_text

        if examples[0]:
            for n, ex in enumerate(examples):
                if ex[-1] == "\n":
                    examples[n] = ex[:-1]

        intro = self.get_intro_message(word, i)

        return intro + main, examples_img(str(word), examples)


def run_twitter_bot(wotd_manager):
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    w = wotd_manager
    now = datetime.datetime.now()
    print(f"Time is currently \t{now}.")
    sleeptime = waittime_between(now, WOTD_H, WOTD_M - 1, WOTD_S)
    print(
        f"{w.dict}-WOTD is scheduled at \t{WOTD_H}H {WOTD_M}M {WOTD_S}S.")
    print(f"Sleeptime: \t\t{datetime.timedelta(seconds=sleeptime)}")
    time.sleep(sleeptime)

    while True:
        word = word_of_the_day(w.dict, w.path)
        print("Today's word is:", word)
        print("Generating message...")
        wotd, incExample = w.wotd_message(word)
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


wotd_m = WotdManagerTwitter('smenob')
run_twitter_bot(wotd_m)
