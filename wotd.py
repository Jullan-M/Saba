import random
import json
from Word import Translation, Meaning, Word


FLAG = {'nb': '🇳🇴',
        'nob': '🇳🇴',
        'nn': '🇳🇴 (nn)',
        'sv': '🇸🇪',
        'swe': '🇸🇪',
        'fi': '🇫🇮',
        'fin': '🇫🇮',
        'en': '🇬🇧',
        'sme': '<SFLAG> (saN)',
        'smn': '<SFLAG> (saI)',
        'sma': '<SFLAG> (saS)',
        'smj': '<SFLAG> (saJ)',
        'sms': '<SFLAG> (saSk)',
        'se': '<SFLAG> (saN)',
        'lat': 'lat'}

WORDCLASS = {'N': 'Substantiiva',
             'V': 'Vearba',
             'Adv': 'Advearba',
             'A': 'Adjektiiva',
             'Pron': 'Pronomen',
             'CC': 'Konjunkšuvdna',
             'Po': 'Postposišuvdna',
             'Pr': 'Preposišuvdna',
             'Interj': 'Interjekšuvdna',
             'Pcle': 'Pcle',
             'mwe': 'Mwe'}


def save_dict_words(d, abc):
    # Iterates through every letter of the sami alphabet
    # and finds every word in a given dictionary.
    # The words are saved to a txt file, separated by \n.

    words = []
    for l in abc:
        print(l)
        res = 0 # search(l) TODO: FIND ALTERNATIVE WAY TO SEARCH DATABASE
        if res == None:
            continue
        lastword = ''
        for w in res:
            if w['dict'] == d and w['term'][0].islower() and lastword != w['term']:
                words.append(w['term'])
                lastword = w['term']

    with open(f"{d}_sorted.txt", "w", encoding="utf-8") as f:
        for w in words[:-1]:
            f.write(f"{w}\n")
        # Write last word in list (without line change)
        f.write(f"{words[-1]}")


def randomize_words(d):
    # Randomize words in dictionary, to be used in WOTD.
    with open(f"{d}_sorted.txt", "r", encoding="utf-8") as f:
        ws = [l.rstrip() for l in f]
    random.shuffle(ws)
    with open(f"{d}_words.txt", "w", encoding="utf-8") as f:
        for w in ws[:-1]:
            f.write(f"{w}\n")
        f.write(f"{ws[-1]}")


def test_words(d):
    # Tests if the dictionary words are parsed correctly,
    with open(f"{d}_words.txt", "r", encoding="utf-8") as f:
        ws = [l.rstrip() for l in f]
        for w in ws:
            print(w, end='')
            word = Word(w, d[:3])
            print(
                f" ({word.meanings[0].pos}): \t{word.meanings[0].trs[0]}", end='')
            if word.meanings[0].trs[0].examples:
                if word.meanings[0].trs[0].examples[0][0]:
                    print(
                        f"\tex: '{word.meanings[0].trs[0].examples[0][0]}'='{word.meanings[0].trs[0].examples[0][1]}'")
            else:
                print()


def next_wotd(d, path, exclDicts=[]):
    # Read WOTD from randomized word file, removes WOTD from file.
    try:
        with open(f"{path}{d}_words.txt", "r", encoding="utf-8") as f:
            head, tail = f.read().split('\n', 1)
        wotd = Word(head, d[:3], exclDicts=exclDicts)
        with open(f"{path}{d}_words.txt", "w", encoding="utf-8") as f:
            f.write(tail)
        return head, wotd
    except ValueError:
        with open(f"{path}{d}_words.txt", "r", encoding="utf-8") as f:
            word = f.read().split('\n')[0]
        if word:
            wotd = Word(word, d[:3], exclDicts=exclDicts)
            with open(f"{path}{d}_words.txt", "w", encoding="utf-8") as f:
                f.write('')
            return word, wotd
        raise Exception(f"{path}{d}_words.txt is empty!")


def blacklist(d, word):
    # Appends word to a blacklist corresponding to the dictionary.
    with open(f"{d}_blacklist.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{word}")


def check_special_wotd(date, lang):
    # Given a date and language, returns a special word and if it has a picture.
    with open("special_words.json", "r", encoding="utf-8") as f:
        sp_ws = json.load(f)
        if date in sp_ws:
            if lang in sp_ws[date]:
                return sp_ws[date][lang]
    return {}


def word_of_the_day(d, path, exclDicts=[]):
    # Returns a Word object of WOTD found in a given dictionary.
    # If the word is in blacklist or the word doesn't exist in dictionary,
    # it will attempt to find a new word, and blacklist the word.
    word, wotd = next_wotd(d, path, exclDicts=exclDicts)
    with open(f"{d}_blacklist.txt", "r", encoding="utf-8") as f:
        bl = f.read().split('\n')

    while word in bl:
        word, wotd = next_wotd(d, path)

    if not wotd.meanings:
        print(f"No meanings were found for the word: {word}.")
        blacklist(d, word)
        return word_of_the_day(d, path)
    return wotd


class WotdManager:
    def __init__(self, d, path):
        self.lang = d[:3]
        self.dict = d
        with open("language_conf.json", "r", encoding="utf-8") as f:
            lang_conf = json.load(f)[self.lang]
        self.wordclass = lang_conf["wordclass"]
        self.path = path

    def get_wotd(self):
        return word_of_the_day(self.dict, self.path)

    def get_intro_message(self, word, count):
        return ""

    def wotd_message(self, word):
        return ""
