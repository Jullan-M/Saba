import urllib
import json

def web2json(url):
    data = urllib.request.urlopen(url).read()
    if (data[0] == 123 and data[2] == 123):  # 123 in ASCII corresponds to {
        return [json.load(data[1:len(data)-1])]
    return json.load(data)


def search(string):
    perenc = urllib.parse.quote(string)  # utf8ize(string)
    results = web2json(
        'https://satni.uit.no:8080/exist/restxq/satni/search?query=' + perenc)
    return results

def get_p_article(term, dictname, src_lang, dest_lang, pos=""):
    perenc = urllib.parse.quote(term)
    postxt = "" if pos else f"?pos={pos}"
    data = urllib.request.urlopen(
        f"https://{dictname}.oahpa.no/paradigm/{src_lang}/{dest_lang}/{perenc}/{postxt}").read()
    return json.load(data)


def get_e_article(term, dictname, src_lang, dest_lang):
    perenc = urllib.parse.quote(term)
    data = urllib.request.urlopen(
        f"https://{dictname}.oahpa.no/lookup/{src_lang}/{dest_lang}/?lookup={perenc}").read()
    return json.load(data)


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
