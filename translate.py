#!/usr/bin/env python3
import sys
import io
import argparse
import urllib.parse
import json
import requests

base = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl={lang1}&tl={lang2}&dt=t&q={text}'

def translate(phrase, lang1, lang2=None):
    if lang2 is None:
        lang1, lang2 = 'auto', lang1
    if phrase == '-':
        phrase = sys.stdin.read()
    phrase = urllib.parse.quote(phrase)
    url = base.format(lang1=lang1, lang2=lang2, text=phrase)
    res = requests.get(url)
    js = json.loads(res.text)
    if not js[0]:
        raise Exception('language not recognized')
    return js[0][0][0]

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
    p.add_argument('lang1')
    p.add_argument('lang2', nargs='?')
    p.add_argument('-u', '--utf8', action='store_true')
    args = p.parse_args()
    if args.utf8:
        sys.stdin = change_encoding(sys.stdin, 'utf-8')
        sys.stdout = change_encoding(sys.stdout, 'utf-8')
    print(translate(args.phrase, args.lang1, args.lang2))
