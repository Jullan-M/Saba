from Word import Translation, Meaning, Word
from utilities import UTF8_CHR, search
import random

FLAG = {'nb': '🇳🇴',
        'nob': '🇳🇴',
        'nn': '🇳🇴 (nn)',
        'sv': '🇸🇪',
        'fi': '🇫🇮',
        'fin': '🇫🇮',
        'en': '🇬🇧',
        'smn': 'smn',
        'sma': 'sma',
        'smj': 'smj',
        'sms': 'sms',
        'se': 'se',
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

EXCL_LANG = ['smn', 'sma', 'smj', 'sms', 'se', 'nb', 'fi', 'nn', 'lat']


def save_dict_words(d):
    # Iterates through every letter of the sami alphabet
    # and finds every word in a given dictionary.
    # The words are saved to a txt file, separated by \n.
    abc = (list('abcdefghijklmnoprstuvz') +
           [UTF8_CHR[l] for l in UTF8_CHR])[:-2]

    words = []
    for l in abc:
        print(l)
        res = search(l)
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
            if word.meanings[0].trs[0].examples[0][0]:
                print(
                    f"\tex: '{word.meanings[0].trs[0].examples[0][0]}'='{word.meanings[0].trs[0].examples[0][1]}'")
            else:
                print()


def get_wotd(d, path):
    # Read WOTD from randomized word file, removes WOTD from file.
    try:
        with open(f"{path}{d}_words.txt", "r", encoding="utf-8") as f:
            head, tail = f.read().split('\n', 1)
        with open(f"{path}{d}_words.txt", "w", encoding="utf-8") as f:
            f.write(tail)
        return head
    except ValueError:
        with open(f"{path}{d}_words.txt", "r", encoding="utf-8") as f:
            word = f.read().split('\n')[0]
        with open(f"{path}{d}_words.txt", "w", encoding="utf-8") as f:
            f.write('')
        if word:
            return word
        raise Exception(f"{path}{d}_words.txt is empty!")


def blacklist(d, word):
    # Appends word to a blacklist corresponding to the dictionary.
    with open(f"{d}_blacklist.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{word}")


def word_of_the_day(d, path):
    # Returns a Word object of WOTD found in a given dictionary.
    # If the word is in blacklist or the word doesn't exist in dictionary,
    # it will attempt to find a new word, and blacklist the word.
    word = get_wotd(d, path)
    with open(f"{d}_blacklist.txt", "r", encoding="utf-8") as f:
        bl = f.read().split('\n')

    while word in bl:
        word = get_wotd(d, path)

    try:
        wotd = Word(word, d[:3])
    except TypeError:
        print(f"No article was found for the word: {word}.")
        blacklist(d, word)
        return word_of_the_day(d, path)

    if not wotd.meanings:
        print(f"No meanings were found for the word: {word}.")
        blacklist(d, word)
        return word_of_the_day(d, path)
    return wotd


'''
print(random_word("smenob"))

word = Word('cakŋa', 'sme')
print(word)

for m in word.meanings:
    if (m.dict == 'smenob'):
        print(f"{word} ({m.pos}) = {m.trs[0]}")
        for ex in m.trs[0].examples:
            print(ex[0])
            print(ex[1])
            print()'''
