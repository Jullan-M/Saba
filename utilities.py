import requests

TW_COLORS = [(29, 161, 242),
             (255, 173, 31),
             (244, 36, 94),
             (121, 75, 196),
             (244, 93, 34),
             (23, 191, 99)]

def get_p_article(term, dictname, src_lang, dest_lang, pos=""):
    postxt = "" if pos else f"?pos={pos}"
    data = requests.get(f"https://{dictname}.oahpa.no/paradigm/{src_lang}/{dest_lang}/{term}/{postxt}", verify=False)
    return data.json()


def get_e_article(term, dictname, src_lang, dest_lang):
    data = requests.get(f"https://{dictname}.oahpa.no/lookup/{src_lang}/{dest_lang}/?lookup={term}", verify=False)
    return data.json()


def waittime_between(time, hrs, mins, secs):
    base = 86400
    h = time.hour - hrs
    m = time.minute - mins
    s = time.second - secs
    diff = h * 3600 + m * 60 + s
    if diff < 0:
        return abs(diff)
    else:
        return base - diff
