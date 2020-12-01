import os
import time
import datetime
import json

from twython import Twython, TwythonError
from dotenv import load_dotenv
from googletrans import Translator
from wotd import word_of_the_day, WotdManager, FLAG, WORDCLASS
from Word import Word
from utilities import waittime_between
from imutils import examples_img

load_dotenv(dotenv_path='twitter_bot/.env')
WOTD_H = int(os.getenv('WOTD_H'))
WOTD_M = int(os.getenv('WOTD_M'))
WOTD_S = int(os.getenv('WOTD_S'))


class WotdManagerTwitter(WotdManager):
    def __init__(self, d, path='twitter_bot/'):
        super().__init__(d, path)
        with open("language_conf.json", "r", encoding="utf-8") as f:
            lang_conf = json.load(f)[self.lang]
        self.tags = lang_conf["tags"]

        with open(f"{path}app_credentials.json", "r") as f:
            app_creds = json.load(f)[self.lang]
        app_key = app_creds["app_key"]
        app_secret = app_creds["app_secret"]
        oauth_token = app_creds["oauth_token"]
        oauth_secret = app_creds["oauth_secret"]
        self.tw = Twython(app_key, app_secret, oauth_token, oauth_secret)
        self.wotd = ""
        self.incExample = False

    def get_intro_message(self, word, count, spec=""):

        intro = spec.replace("<WORD>", f"#{word}")
        hashtagged = " ".join(["#" + w for w in str(word).split(" ")])

        if self.lang == 'sme':
            if not intro:
                intro = f"Otná sátni lea {hashtagged}!"
            intro += "\nSánis lea"
            intro = intro + \
                f"t {count} mearkkašumit:\n" if (
                    count > 1) else intro + f" okta mearkkašupmi:\n"
            return intro

        elif self.lang == 'sma':
            if not intro:
                intro = f"Daen biejjien baakoe lea {hashtagged}!"
            intro += "\nBaakoen lea"
            intro = intro + \
                f"h {count} goerkesimmieh:\n" if (
                    count > 1) else intro + f" akte goerkesimmie:\n"
            return intro

    def wotd_message(self, word):
        try:
            trns = Translator(service_urls=['translate.googleapis.com'])
            main = ""
            lastpos = ""
            lastword = ""
            lastdesc = ""
            examples = ["", "", ""]
            i = 0
            for m in word.meanings:
                trs_text = ""
                for tr in m.trs:
                    if (lastword == str(tr) and lastdesc == tr.desc):
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
                            tr_en = ", ".join([w.text.replace("to ", "") for w in trns.translate(
                                ["å " + v for v in str(tr).split(", ")], src='no', dest='en')])
                        desc_en = trns.translate(
                            tr.desc, src='no', dest='en').text if tr.desc else ''
                        trs_text += f" {FLAG[tr.lang]} {tr} {tr.desc}  →  {FLAG['en']} {tr_en} {desc_en}\n"
                        for ex in tr.examples:
                            ex_en = trns.translate(ex[1], src='no', dest='en').text
                            examples[0] += f"– {ex[0]}\n"
                            examples[1] += f"– {ex[1]}\n"
                            examples[2] += f"– {ex_en}\n"
                    elif tr.lang == 'fin' or tr.lang == 'fi':
                        tr_en = ", ".join([w.text for w in trns.translate(
                            str(tr).split(", "), src='fi', dest='en')])
                        desc_en = trns.translate(
                            tr.desc, src='no', dest='en').text if tr.desc else ''
                        trs_text += f" {FLAG[tr.lang]} {tr} {tr.desc}  →  {FLAG['en']} {tr_en} {desc_en}\n"
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

            if main[-1] == "\n":
                main = main[:-1]

            intro = self.get_intro_message(word, i)

            tgs = "\n" + " ".join(self.tags)
            if len(main) + len(tgs) < 280:
                main += tgs

            return intro + main, examples_img(self.lang, str(word), examples)
        except AttributeError:
            print("AttributeError. Trying again in 0.1 seconds...")
            time.sleep(0.1)
            return self.wotd_message(word)



def run_twitter_bot(wotd_manager):
    now = datetime.datetime.now()
    print(f"Time is currently \t{now}.")
    sleeptime = waittime_between(now, WOTD_H, WOTD_M - 1, WOTD_S)
    print(
        f"WOTD is scheduled at \t{WOTD_H}H {WOTD_M}M {WOTD_S}S.")
    for w in wotd_m:
        print(w.lang)
    print(f"Sleeptime: \t\t{datetime.timedelta(seconds=sleeptime)}")
    time.sleep(sleeptime)

    while True:
        print("Generating WOTDs...")
        for w in wotd_manager:
            word = word_of_the_day(w.dict, w.path, exclDicts=["gtsmesmn"])
            print(f"{w.lang}-WOTD: {word}")
            w.wotd, w.incExample = w.wotd_message(word)
            while len(w.wotd) >= 280: # Do not exceed Twitter max character limit
                print(f"String length too long ({len(w.wotd)}): removing last line. ", end="")
                w.wotd = w.wotd[:(w.wotd.rfind('\n'))]
                print(f"Current length: {len(w.wotd)}")


        now = datetime.datetime.now()
        print(f"Finished generating WOTDs at {now}")
        sleeptime = waittime_between(now, WOTD_H, WOTD_M, WOTD_S)
        print(f"sleeping for {sleeptime}s...")
        time.sleep(sleeptime)
        for w in wotd_manager:
            while True:
                try:
                    if w.incExample:
                        example_file = open(
                            f'media/examples_{w.lang}.png', 'rb')
                        response = w.tw.upload_media(media=example_file)
                        w.tw.update_status(status=w.wotd, media_ids=[
                            response['media_id']])
                        print(
                            f"{w.lang}-WOTD was sent to Twitter with example.\n")
                    else:
                        w.tw.update_status(status=w.wotd)
                        print(f"{w.lang}-WOTD was sent to Twitter.\n")
                    break
                except TwythonError:
                    # If status update fails, try again in 30 sec.
                    time.sleep(30)

        now = datetime.datetime.now()
        time.sleep(waittime_between(now, WOTD_H, WOTD_M - 1, WOTD_S))


wotd_m = [WotdManagerTwitter(d) for d in ['smenob', 'smanob']]
run_twitter_bot(wotd_m)
