#!/usr/bin/env python3
import sys
import urllib.parse
import requests
import bs4

def translate(phrase, lang1, lang2=None, *, utf8=False):
    if not lang2:
        lang1, lang2 = 'english', lang1
    lang1, lang2 = lang1.lower(), lang2.lower()
    base = 'http://translate.reference.com/{}/{}/{}/'
    if phrase == '-':
        if utf8:
            phrase = sys.stdin.buffer.read().decode()
        else:
            phrase = sys.stdin.read()
    phrase = urllib.parse.quote(phrase)
    url = base.format(lang1, lang2, phrase)
    res = requests.get(url)
    doc = bs4.BeautifulSoup(res.text, 'html.parser')
    ta = doc.find(id='clipboard-text')
    if ta:
        if utf8:
            sys.stdout.buffer.write(ta.text.encode() + b'\n')
        else:
            print(ta.text)
    else:
        print('Error: language not found')

if __name__ == '__main__':
    utf8 = '--utf8' in sys.argv
    if utf8:
        sys.argv.remove('--utf8')
    translate(*sys.argv[1:], utf8=utf8)
