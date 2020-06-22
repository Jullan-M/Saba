from Word import Translation, Meaning, Word
from utilities import UTF8_CHR, search, get_w_article
import numpy as np


def save_dict_words(d):
    abc = list('abcdefghijklmnoprstuvz') + \
        [UTF8_CHR[:-2][l] for l in UTF8_CHR[:-2]]

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
        for w in words:
            f.write(w + '\n')
    f.close()


def test_words(d):
    with open(f"{d}_words.txt", "r", encoding="utf-8") as f:
        ws = [l.rstrip() for l in f]
        for w in ws:
            print(w, end='')
            w_article = get_w_article(w)
            word = Word(w_article, d[:3])
            print(
                f" ({word.meanings[0].pos}): \t{word.meanings[0].trs[0]}", end='')
            if word.meanings[0].trs[0].examples[0][0]:
                print(
                    f"\tex: '{word.meanings[0].trs[0].examples[0][0]}'='{word.meanings[0].trs[0].examples[0][1]}'")
            else:
                print()
    f.close()


test_words('smenob')

word_article = get_w_article('cakŋa')
word = Word(word_article, 'sme')
print(word)

for m in word.meanings:
    if (m.dict == 'smenob'):
        print(f"{word} ({m.pos}) = {m.trs[0]}")
        for ex in m.trs[0].examples:
            print(ex[0])
            print(ex[1])
            print()
