from Word import Translation, Meaning, Word
from utilities import UTF8_CHR, search
import random


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
    with open(f"{d}_blacklist.txt", "w", encoding="utf-8") as f:
        f.write(f"{word}\n")


def word_of_the_day(d):
    word = random_word(d)
    with open(f"{d}_blacklist.txt", "r", encoding="utf-8") as f:
        bl = f.read().split('\n')

    while word in bl:
        word = random_word(d)

    blacklist(d, word)

    wotd = Word(word, d[:3])
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
