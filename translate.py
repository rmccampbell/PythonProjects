#!/usr/bin/env python3
import sys
import io
import argparse
import urllib.parse
import requests

langs = {'afrikaans': 'af', 'albanian': 'sq', 'arabic': 'ar',
         'azerbaijani': 'az', 'basque': 'eu', 'belarusian': 'be',
         'bengali': 'bn', 'bulgarian': 'bg', 'catalan': 'ca',
         'chinese simplified': 'zh-cn', 'chinese traditional': 'zh-tw',
         'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 'dutch': 'nl',
         'english': 'en', 'esperanto': 'eo', 'estonian': 'et',
         'filipino': 'tl', 'finnish': 'fi', 'french': 'fr', 'galician': 'gl',
         'georgian': 'ka', 'german': 'de', 'greek': 'el', 'gujarati': 'gu',
         'haitian creole': 'ht', 'hebrew': 'iw', 'hindi': 'hi',
         'hungarian': 'hu', 'icelandic': 'is', 'indonesian': 'id',
         'irish': 'ga', 'italian': 'it', 'japanese': 'ja', 'kannada': 'kn',
         'korean': 'ko', 'latin': 'la', 'latvian': 'lv', 'lithuanian': 'lt',
         'macedonian': 'mk', 'malay': 'ms', 'maltese': 'mt', 'norwegian': 'no',
         'persian': 'fa', 'polish': 'pl', 'portuguese': 'pt', 'romanian': 'ro',
         'russian': 'ru', 'serbian': 'sr', 'slovak': 'sk', 'slovenian': 'sl',
         'spanish': 'es', 'swahili': 'sw', 'swedish': 'sv', 'tamil': 'ta',
         'telugu': 'te', 'thai': 'th', 'turkish': 'tr', 'ukrainian': 'uk',
         'urdu': 'ur', 'vietnamese': 'vi', 'welsh': 'cy', 'yiddish': 'yi'}

rlangs = {v: k for k, v in langs.items()}

apiurl = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl={lang1}&tl={lang2}&dt=t&q={text}'

def translate(phrase, lang1='auto', lang2=None, return_lang=False):
    if lang2 is None:
        lang1, lang2 = 'auto', lang1
    if lang2 == 'auto':
        lang2 = 'english'
    lang1 = langs.get(lang1.lower(), lang1)
    lang2 = langs.get(lang2.lower(), lang2)
    phrase = urllib.parse.quote(phrase)
    url = apiurl.format(lang1=lang1, lang2=lang2, text=phrase)
    res = requests.get(url)
    res.raise_for_status()
    js = res.json()
    translated = ''.join(part[0] for part in js[0])
    if return_lang:
        return translated, rlangs.get(js[2], js[2])
    return translated

def change_encoding(file, encoding='utf-8'):
    if file.encoding == encoding:
        return file
    file2 = io.TextIOWrapper(file.buffer, encoding, file.errors,
                             line_buffering=file.line_buffering)
    file2.mode = file.mode
    file.detach()
    return file2

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phrase')
    p.add_argument('lang1', nargs='?', default='auto')
    p.add_argument('lang2', nargs='?')
    p.add_argument('-l', '--print-lang', action='store_true')
    p.add_argument('-u', '--utf8', action='store_true')
    args = p.parse_args()
    if args.utf8:
        sys.stdin = change_encoding(sys.stdin, 'utf-8')
        sys.stdout = change_encoding(sys.stdout, 'utf-8')
    if args.phrase == '-':
        args.phrase = sys.stdin.read()
    try:
        text, lang = translate(args.phrase, args.lang1, args.lang2, True)
        if args.print_lang:
            print(lang)
        print(text)
    except Exception as e:
        sys.exit('Error: {}: {}'.format(type(e).__name__, e))
