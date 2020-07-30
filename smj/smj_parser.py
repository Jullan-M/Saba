from bs4 import BeautifulSoup
import json

abc = "a1bcdefghijklmnoprstuvwæ2"
smj_dict = {}
for l in abc:
    with open(f"smj2nob/{l}_smj2nob.html", encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')
    odd_row = soup.findAll("tr", {"class": "normalRow"})
    even_row = soup.findAll("tr", {"class": "alternateRow"})
    for o, e in zip(odd_row, even_row):
        o_entry = o.text.split("\n")
        e_entry = e.text.split("\n")
        if o_entry[1]:
            smj_dict[o_entry[1][:-1]] = o_entry[2]
        if e_entry[1]:
            smj_dict[e_entry[1][:-1]] = e_entry[2]

with open("smjnob_dict.json", "w", encoding="utf-8") as f:
    json.dump(smj_dict, f, ensure_ascii=False)

with open("smjnob_words.txt", "w", encoding="utf-8") as f:
    for e in smj_dict:
        f.write(f"{e}\n")