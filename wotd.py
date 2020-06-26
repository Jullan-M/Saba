from Word import Translation, Meaning, Word
from utilities import UTF8_CHR, search
from googletrans import Translator
import random

FLAG = {'nb': '🇳🇴',
        'nob': '🇳🇴',
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
             'Pr': 'Preposišuvdna'}

SAMI_LANG = ['smn', 'sma', 'smj', 'sms', 'se', 'nb']


def save_dict_words(d):
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

    with open(f"{d}_words.txt", "w", encoding="utf-8") as f:
        for w in words[:-1]:
            f.write(f"{w}\n")
        f.write(f"{words[-1]}")


def test_words(d):
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


def random_word(d):
    with open(f"{d}_words.txt", "r", encoding="utf-8") as f:
        words = f.read().split('\n')
    return random.choice(words)


def blacklist(d, word):
    with open(f"{d}_blacklist.txt", "a", encoding="utf-8") as f:
        f.write(f"{word}\n")


def word_of_the_day(d):
    word = random_word(d)
    with open(f"{d}_blacklist.txt", "r", encoding="utf-8") as f:
        bl = f.read().split('\n')

    while word in bl:
        word = random_word(d)

    blacklist(d, word)

    wotd = Word(word, d[:3])
    if not wotd.meanings:
        return word_of_the_day(d)
    return wotd


def underscore_word(string, word):
    return string.replace(word.capitalize(), f'__{word.capitalize()}__').replace(word, f'__{word}__')


def wotd_message(word):
    trns = Translator()
    main = ""
    lastpos = ""
    lastword = ""
    lastdesc = ""
    i = 0
    for m in word.meanings:
        if lastpos != m.pos:
            i += 1
            main += f"\t{i}. {WORDCLASS[m.pos]}\n"
            lastpos = m.pos

        for tr in m.trs:
            if tr.lang in SAMI_LANG or (lastword == str(tr) and lastdesc == tr.desc):
                continue
            lastword = str(tr)
            lastdesc = tr.desc

            if tr.lang == 'nob':
                tr_en = trns.translate(str(tr), src='no', dest='en').text
                desc_en = trns.translate(
                    tr.desc, src='no', dest='en').text if tr.desc else ''
                main += f"\t\t{FLAG[tr.lang]} {tr} {tr.desc}\t→\t{FLAG['en']} {tr_en} {desc_en}\n"
                for n, ex in enumerate(tr.examples):
                    ex_en = trns.translate(ex[1], src='no', dest='en').text
                    main += f"> <:samiflag:725121267933511742> *{underscore_word(ex[0], str(word))}*\n"
                    main += f"> {FLAG[tr.lang]} *{underscore_word(ex[1], str(tr))}*\n"
                    main += f"> {FLAG['en']} *{underscore_word(ex_en, tr_en)}*\n"
                    if (n != len(tr.examples)-1):
                        main += "\n"
            else:
                main += f"\t\t{FLAG[tr.lang]} {tr}\n"

    intro = f"<@&418533166878425103>, otná sátni lea **{word}**!\n Sánis lea"
    intro = intro + \
        f"t {i} mearkkašumit:\n" if (
            i > 1) else intro + f" okta mearkkašupmi:\n"
    return intro + main


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
