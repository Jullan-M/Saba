# Used for parsing word articles from UiT Divvun database
from utilities import get_w_article


class Translation:
    def __init__(self, translation):
        self.tword = translation['t'][0]['#text'] if isinstance(
            translation['t'], list) else translation['t']['#text']
        self.pos = self.find_pos(translation)
        self.lang = translation['xml:lang']
        self.desc = f"({translation['re']})" if 're' in translation else ''
        self.examples = self.find_examples(translation)

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
