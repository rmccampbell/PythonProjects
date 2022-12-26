#!/usr/bin/env python3
import sys, random, unicodedata, argparse

def nospace(s):
    return ''.join(s.split())

HIRAGANA = nospace('''
あかさたなはまやらわん
いきしちにひみ　り
うくすつぬふむゆる
えけせてねへめ　れ
おこそとのほもよろを
''')

HIRAGANA_EXT = nospace('''
がざだばぱ
ぎじぢびぴ
ぐずづぶぷ
げぜでべぺ
ごぞどぼぽ
''')

KATAKANA = nospace('''
アカサタナハマヤラワン
イキシチニヒミ　リ
ウクスツヌフムユル
エケセテネヘメ　レ
オコソトノホモヨロヲ
''')

KATAKANA_EXT = nospace('''
ガザダバパ
ギジヂビピ
グズヅブプ
ゲゼデベペ
ゴゾドボポ
''')

IRREGULAR = {'si': 'shi', 'ti': 'chi', 'tu': 'tsu', 'hu': 'fu',
             'zi': 'ji', 'di': 'ji', 'du': 'zu'}

charsets = {'hiragana': HIRAGANA, 'hiragana-ext': HIRAGANA_EXT,
            'hiragana-all': HIRAGANA + HIRAGANA_EXT,
            'katakana': KATAKANA, 'katakana-ext': KATAKANA_EXT,
            'katakana-all': KATAKANA + KATAKANA_EXT,
            'all': HIRAGANA + HIRAGANA_EXT + KATAKANA + KATAKANA_EXT}

def kana_name(c):
    name = unicodedata.name(c).split()[-1].lower()
    return IRREGULAR.get(name, name)

def print_double(s):
    print('\x1b#3' + s)
    print('\x1b#4' + s)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('charset', nargs='?', default='hiragana')
    p.add_argument('-d', '--double-height', action='store_true',
                   help='use dec double-height characters')
    args = p.parse_args()
    charset = ''.join(charsets[s.lower()] for s in args.charset.split('+'))
    try:
        while True:
            c = random.choice(charset)
            if args.double_height:
                print_double(c)
            else:
                print(c)
            name = kana_name(c)
            if input().lower() == name:
                print('Correct!')
            else:
                print('Incorrect:', name)
    except (KeyboardInterrupt, EOFError):
        pass
