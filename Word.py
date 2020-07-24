# Used for parsing word articles from UiT Divvun database
from utilities import get_w_article, get_p_article, get_e_article

DICTNAMES = {"sme": "sanit",
             "sma": "baakoeh",
             "sms": "saan",
             "smn": "saanih"}

PREF_DEST = {"sme": "nob",
             "sma": "nob",
             "sms": "nob",
             "smn": "sme"}


class Translation:
    def __init__(self, translation):
        self.tword = self.find_twords(translation)
        self.pos = self.find_pos(translation)
        self.lang = translation['xml:lang']
        self.desc = f"({translation['re']})" if 're' in translation else ''
        self.examples = self.find_examples(translation)

    def find_twords(self, translation):
        tword = ""
        if isinstance(translation['t'], list):
            for w in translation['t'][:-1]:
                tword += f"{w['#text']}, "
            tword += translation['t'][-1]['#text']
        else:
            tword = translation['t']['#text']
        return tword

    def find_examples(self, translation):
        if not ('xg' in translation):
            return []

        if isinstance(translation['xg'], list):
            return [[ex['x'], ex['xt']] for ex in translation['xg']]
        else:
            return [[translation['xg']['x'], translation['xg']
                     ['xt']]]

    def find_pos(self, translation):
        if isinstance(translation['t'], list):
            return translation['t'][0]['pos']
        elif ('pos' in translation['t']):
            return translation['t']['pos']
        return ''

    def __str__(self):
        return self.tword


class Meaning:
    def __init__(self, meaning):
        self.pos = meaning['pos']
        self.dict = meaning['dict']
        self.trs = self.find_translations(meaning)

    def find_translations(self, meaning):
        trs = meaning['tg']
        translations = [Translation(tr) for tr in trs] if isinstance(
            trs, list) else [Translation(trs)]
        return translations


def isValidLanguage(lang, d):
    return d[:3] == lang or (lang == 'sme' and d == 'termwiki')


class Word:
    def __init__(self, word, lang):
        w_article = get_w_article(word)
        self.word = word
        self.lang = lang
        self.meanings = self.find_meanings(w_article)

    def find_meanings(self, w_article):
        meanings = []
        for el in w_article:
            if isValidLanguage(self.lang, el['dict']):
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


