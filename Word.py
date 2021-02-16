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

with open('language_conf.json', 'r', encoding="utf-8") as f:
    lang_conf = json.load(f)

headers = {
    'Content-Type': 'application/json',
}

query = """
query AllArticles($lemma: String!, $wantedLangs: [String]!, $wantedDicts: [String]!) {
    dictEntryList(exact: $lemma, wanted: $wantedLangs, wantedDicts: $wantedDicts) {
        dictName
        targetLang
        lookupLemmas {
            edges {
                node {
                    lemma
                    language
                    pos
                }
            }
        }
        translationGroups {
            translationLemmas {
                edges {
                    node {
                        lemma
                        language
                        pos
                    }
                }
            }
            exampleGroups {
                example
                translation
            }
            restriction {
                restriction
            }
        }
    }
    conceptList(exact: $lemma, wanted: $wantedLangs) {
        name
        collections
        definition
        explanation
        terms {
            note
            source
            status
            expression {
                lemma
                language
                pos
            }
        }
    }
}
"""

word_query = {
    "operationName": "AllArticles",
    "variables": {
        "wantedLangs": ["sme", "smj", "smn", "sms", "fin", "nob", "swe", "lat", "eng", "nno", "sma"],
    },
    "query": query
}


class Translation:
    def __init__(self, translation):
        self.tword = self.find_twords(translation)
        self.pos = translation["translationLemmas"]["edges"][0]["node"]["pos"]
        self.lang = translation["translationLemmas"]["edges"][0]["node"]["language"]
        self.desc = f'({translation["restriction"]["restriction"]})' if translation["restriction"] else ''
        self.examples = [[ex["example"], ex["translation"]]
                         for ex in translation["exampleGroups"]] if (translation["exampleGroups"]) else []
        # Do a sanity check on examples, in case they are empty
        if not all( [(True if el1 and el2 else False) for el1, el2 in self.examples] ):
            self.examples = []

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
        self.dict = meaning["dictName"]
        self.trs = self.find_translations(meaning)

    def find_translations(self, meaning):
        trs = meaning["translationGroups"]
        translations = [Translation(tr) for tr in trs]
        return translations


class Word:
    def __init__(self, word, lang, exclDicts=[]):
        word_query["variables"]["lemma"] = word
        word_query["variables"]["wantedDicts"] = lang_conf[lang]["wantedDicts"]

        if exclDicts:
            for excl in exclDicts:
                if excl in word_query["variables"]["wantedDicts"]:
                    word_query["variables"]["wantedDicts"].remove(excl)

        response = requests.post(
            'https://satni.uit.no/newsatni/', headers=headers, data=json.dumps(word_query))

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
