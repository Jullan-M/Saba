import requests
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

headers = {
    'Content-Type': 'application/json',
}

data = '{"operationName":"AllArticles","variables":{"lemma":"mann","wantedLangs":["sme","smj","smn","sms","fin","nob","swe","lat","eng","nno","sma"],"wantedDicts":["termwiki","gtsmenob","gtnobsme","gtnobsma","gtsmanob","gtsmefin","gtfinsme","gtsmesmn","gtsmnsme","sammallahtismefin","gtfinsmn","gtsmnfin"]},"query":"query AllArticles($lemma: String!, $wantedLangs: [String]!, $wantedDicts: [String]!) {\\n dictEntryList(exact: $lemma, wanted: $wantedLangs, wantedDicts: $wantedDicts) {\\n dictName\\n srcLang\\n targetLang\\n lookupLemmas {\\n edges {\\n node {\\n lemma\\n language\\n pos\\n __typename\\n }\\n __typename\\n }\\n __typename\\n }\\n translationGroups {\\n translationLemmas {\\n edges {\\n node {\\n lemma\\n language\\n pos\\n __typename\\n }\\n __typename\\n }\\n __typename\\n }\\n restriction {\\n restriction\\n attributes\\n __typename\\n }\\n exampleGroups {\\n example\\n translation\\n __typename\\n }\\n __typename\\n }\\n __typename\\n }\\n conceptList(exact: $lemma, wanted: $wantedLangs) {\\n name\\n collections\\n definition\\n explanation\\n terms {\\n note\\n source\\n status\\n expression {\\n lemma\\n language\\n pos\\n __typename\\n }\\n __typename\\n }\\n __typename\\n }\\n}\\n"}'

response = requests.post(
    'https://satni.uit.no/newsatni/', headers=headers, data=data)
with open('data.json', 'w') as f:
    json.dump(response.json(), f)


def utf8ize(string):
    # Deprecated function, replaced by urllib.parse.quote()
    utf8str = string
    for l in UTF8_CHR:
        utf8str = utf8str.replace(l, UTF8_CHR[l])
    return utf8str


def web2json(url):
    data = request.urlopen(url).read()
    if (data[0] == 123 and data[2] == 123):  # 123 in ASCII corresponds to {
        return [json.loads(data[1:len(data)-1])]
    return json.loads(data)


def search(string):
    perenc = parse.quote(string)  # utf8ize(string)
    results = web2json(
        'https://satni.uit.no/newsatni/exist/restxq/satni/search?query=' + perenc)
    return results


def get_w_article(term):
    perenc = parse.quote(term)  # utf8ize(term)
    article = web2json(
        'https://satni.uit.no/newsatni/exist/restxq/satni/article/' + perenc)
    return article


def get_p_article(term, dictname, src_lang, dest_lang, pos=""):
    perenc = parse.quote(term)
    postxt = "" if pos else f"?pos={pos}"
    data = request.urlopen(
        f"https://{dictname}.oahpa.no/paradigm/{src_lang}/{dest_lang}/{perenc}/{postxt}").read()
    return json.loads(data)


def get_e_article(term, dictname, src_lang, dest_lang):
    perenc = parse.quote(term)
    data = request.urlopen(
        f"https://{dictname}.oahpa.no/lookup/{src_lang}/{dest_lang}/?lookup={perenc}").read()
    return json.loads(data)


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
