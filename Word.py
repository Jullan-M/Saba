# Used for parsing word articles from UiT Divvun database
import json
import requests
from utilities import get_p_article, get_e_article

DICTNAMES = {"sme": "sanit",
             "sma": "baakoeh",
             "sms": "saan",
             "smn": "saanih"}

PREF_DEST = {"sme": "nob",
             "sma": "nob",
             "sms": "nob",
             "smn": "sme"}

with open('language_conf.json', 'r') as f:
    lang_conf = json.load(f)

class Translation:
    def __init__(self, translation):
        self.tword = self.find_twords(translation)
        self.pos = translation["translationLemmas"]["edges"][0]["node"]["pos"]
        self.lang = translation["translationLemmas"]["edges"][0]["node"]["language"]
        self.desc = f'({translation["restriction"]["restriction"]})' if translation["restriction"] else ''
        self.examples = [[ex["example"], ex["translation"]] for ex in translation["exampleGroups"]] if (translation["exampleGroups"]) else []

    def find_twords(self, translation):
        tword = ""
        if translation["translationLemmas"]["edges"]:
            for w in translation["translationLemmas"]["edges"][:-1]:
                tword += f'{w["node"]["lemma"]}, '
            tword += translation["translationLemmas"]["edges"][-1]["node"]["lemma"]
        return tword

    def __str__(self):
        return self.tword


class Meaning:
    def __init__(self, meaning):
        self.pos = meaning["lookupLemmas"]["edges"][0]["node"]["pos"]
        self.dict = meaning["srcLang"] + meaning["targetLang"]
        self.trs = self.find_translations(meaning)

    def find_translations(self, meaning):
        trs = meaning["translationGroups"]
        translations = [Translation(tr) for tr in trs] # if isinstance(trs, list) else [Translation(trs)]
        return translations

class Word:
    def __init__(self, word, lang, exclDicts=[]):
        headers = {
            'Content-Type': 'application/json',
        }

        data = {
            "operationName": "AllArticles",
            "variables": {
                "lemma": word,
                "wantedLangs": ["sme","smj","smn","sms","fin","nob","swe","lat","eng","nno","sma"],
                "wantedDicts": lang_conf[lang]["wantedDicts"]
            },
            "query": "query AllArticles($lemma: String!, $wantedLangs: [String]!, $wantedDicts: [String]!) {\n dictEntryList(exact: $lemma, wanted: $wantedLangs, wantedDicts: $wantedDicts) {\n dictName\n srcLang\n targetLang\n lookupLemmas {\n edges {\n node {\n lemma\n language\n pos\n __typename\n }\n __typename\n }\n __typename\n }\n translationGroups {\n translationLemmas {\n edges {\n node {\n lemma\n language\n pos\n __typename\n }\n __typename\n }\n __typename\n }\n restriction {\n restriction\n attributes\n __typename\n }\n exampleGroups {\n example\n translation\n __typename\n }\n __typename\n }\n __typename\n }\n conceptList(exact: $lemma, wanted: $wantedLangs) {\n name\n collections\n definition\n explanation\n terms {\n note\n source\n status\n expression {\n lemma\n language\n pos\n __typename\n }\n __typename\n }\n __typename\n }\n}\n"
        }
        
        if exclDicts:
            for excl in exclDicts:
                data["variables"]["wantedDicts"].remove(excl)

        response = requests.post(
            'https://satni.uit.no/newsatni/', headers=headers, data=json.dumps(data))

        w_article = response.json()["data"]["dictEntryList"]
        
        self.word = word
        self.lang = lang
        self.meanings = self.find_meanings(w_article)

    def find_meanings(self, w_article):
        meanings = []
        for el in w_article:
            meanings.append(Meaning(el))
        return meanings

    def __str__(self):
        return self.word


class Paradigm:
    def __init__(self, word, lang):
        p_article = get_p_article(word, DICTNAMES[lang], lang, PREF_DEST[lang])
        self.word = word
        self.lang = lang
        self.paradigms = [self.parse_paradigm(
            p) for p in p_article["paradigms"]]

    def parse_paradigm(self, p):
        paradigm = {}
        for e in p:
            paradigm[e[3]] = e[0]
        return paradigm

class Inflection:
    def __init__(self, word, lang):
        e_article = get_e_article(word, DICTNAMES[lang], lang, PREF_DEST[lang])
        self.word = word 
        self.lang = lang
        self.inflections = self.parse_inflections(e_article)
    
    def parse_inflections(self, e_article):
        inflections = []
        for inf in e_article["tags"]:
            entry = [inf[0], inf[1].replace(f"{inf[0]} ", "")]
            if entry not in inflections:
                inflections.append(entry)
        return inflections