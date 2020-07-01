import urllib.request
import json

UTF8_CHR = {'á': '%C3%A1',
            'č': '%C4%8D',
            'đ': '%C4%91',
            'ŋ': '%C5%8B',
            'š': '%C5%A1',
            'ŧ': '%C5%A7',
            'ž': '%C5%BE',
            ' ': '%20',
            'ø': '%C3%B8'
            }


def utf8ize(string):
    utf8str = string
    for l in UTF8_CHR:
        utf8str = utf8str.replace(l, UTF8_CHR[l])
    return utf8str


def web2json(url):
    data = urllib.request.urlopen(
        url).read()
    if (data[0] == 123 and data[2] == 123):  # 123 in ASCII corresponds to {
        return [json.loads(data[1:len(data)-1])]
    return json.loads(data)


def search(string):
    utf8str = utf8ize(string)
    results = web2json(
        'http://satni.uit.no:8080/exist/restxq/satni/search?query=' + utf8str)
    return results


def get_w_article(term):
    utf8str = utf8ize(term)
    article = web2json(
        'http://satni.uit.no:8080/exist/restxq/satni/article/' + utf8str)
    return article


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
