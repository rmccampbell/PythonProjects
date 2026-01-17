#!/usr/bin/env python3
import sys, math
from fractions import Fraction
from decimal import Decimal

ones = [
    'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
    'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
    'sixteen', 'seventeen', 'eighteen', 'nineteen'
]

tens = [
    '', 'ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
    'eighty', 'ninety'
]

thousands = [
    '', 'thousand', 'million', 'billion', 'trillion', 'quadrillion',
    'quintillion', 'sextillion', 'septillion', 'octillion', 'nonillion',

    'decillion', 'undecillion', 'duodecillion', 'tredecillion',
    'quattuordecillion', 'quinquadecillion', 'sedecillion', 'septendecillion',
    'octodecillion', 'novendecillion',

    'vigintillion', 'unvigintillion', 'duovigintillion', 'tresvigintillion',
    'quattuorvigintillion', 'quinquavigintillion', 'sesvigintillion',
    'septemvigintillion', 'octovigintillion', 'novemvigintillion',

    'trigintillion', 'untrigintillion', 'duotrigintillion', 'trestrigintillion',
    'quattuortrigintillion', 'quinquatrigintillion', 'sestrigintillion',
    'septentrigintillion', 'octotrigintillion', 'noventrigintillion',

    'quadragintillion'
]

ones_map = {n: i for i, n in enumerate(ones)}
tens_map = {n: i for i, n in enumerate(tens) if n}
thousands_map = {n: i for i, n in enumerate(thousands) if n}

def smalln2words(n):
    if n < 0 or n >= 1000:
        raise ValueError('n must be between 0 and 999')
    h, n = divmod(n, 100)
    s = ones[h] + ' hundred ' if h else ''
    if n < 20:
        s += ones[n] if n or not h else ''
    else:
        t, n = divmod(n, 10)
        s += tens[t] + ' '
        s += ones[n] if n else ''
    return s.strip()

##def num2words(n, e=0):
##    sgn = 'negative ' if n < 0 else ''
##    n, r = divmod(abs(n), 1000)
##    s = smalln2words(r) + (' ' + thousands[e] if e else '')
##    if n:
##        s = num2words(n, e+1) + (' ' + s if r else '')
##    return sgn + s

def num2words(n, limit_denom=1000000):
    sgn, n = n < 0, abs(n)
    if not isinstance(n, int):
        n, f = int(n), n % 1
        if f:
            return frac2words(sgn, n, f, limit_denom)
    n, r = divmod(n, 1000)
    e = 0
    ss = [smalln2words(r)] if r or not n else []
    while n:
        n, r = divmod(n, 1000)
        e += 1
        if r:
            ss += [thousands[e], smalln2words(r)]
    if sgn:
        ss.append('negative')
    return ' '.join(ss[::-1])


def frac2words(sgn, i, f, limit_denom=1000000):
    f = Fraction(f)
    if limit_denom:
        f = f.limit_denominator(limit_denom)
    num, den = f.numerator, f.denominator
    numw, denw = num2words(num), num2words(den)
    if denw.endswith('one'):
        denw = denw[:-3] + 'first'
    elif denw.endswith('two'):
        denw = denw[:-3] + ('half' if den == 2 else 'second')
    elif denw.endswith('three'):
        denw = denw[:-5] + 'third'
    elif denw.endswith('ty'):
        denw = denw[:-1] + 'ieth'
    else:
        denw += 'th'
    if num > 1:
        denw += 's'
    sgnw = 'negative ' if sgn else ''
    if i:
        return '{}{} and {} {}'.format(sgnw, num2words(i), numw, denw)
    return '{}{} {}'.format(sgnw, numw, denw)


def words2num(s):
    n = 0
    x = 0
    last_type = ''
    last_thousand = 0
    try:
        return int(s.replace(',', ''))
    except ValueError:
        pass
    s = s.replace('-', ' ')
    for w in s.lower().split():
        if w in ones_map:
            if last_type == 'ones' or x % 10:
                raise ValueError('two ones in a row')
            num = ones_map[w]
            if (last_type == 'tens' or x % 100) and num >= 10:
                raise ValueError('two tens in a row')
            x += num
            last_type = 'ones'
        elif w in tens_map:
            if last_type == 'ones' or x % 10:
                raise ValueError('tens after ones')
            if last_type == 'tens' or x % 100:
                raise ValueError('two tens in a row')
            x += tens_map[w] * 10
            last_type = 'tens'
        elif w == 'hundred':
            if last_type != 'ones' or x >= 10:
                raise ValueError('"hundred" not preceded by ones')
            x *= 100
            last_type = 'hundreds'
        elif w in thousands_map:
            if not last_type:
                raise ValueError('thousands unit not preceded by number')
            elif last_type == 'thousands':
                raise ValueError('two thousands in a row')
            thousand = thousands_map[w]
##            if n % 1000**(thousand + 1):
            if last_thousand and thousand >= last_thousand:
                raise ValueError('thousands not in order')
            n += x * 1000**thousand
            last_type = 'thousands'
            last_thousand = thousand
            x = 0
        else:
            try:
                m = Decimal(w)
            except:
                raise ValueError('invalid number')
            if m >= 1000:
                raise ValueError('numeric literal greater than 999')
            if m >= 100 and last_type == 'hundreds':
                raise ValueError('two hundreds in a row')
            if m >= 10 and (last_type == 'tens' or x % 100):
                raise ValueError('two tens in a row')
            if last_type == 'ones' or x % 10:
                raise ValueError('two ones in a row')
            x += m
            last_type = 'ones'
    n += x
    return int(n)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('args', nargs='*')
    p.add_argument('-w', '--words2num', action='store_true')
    args = p.parse_args()
    for s in args.args or sys.stdin:
        if args.words2num:
            print(words2num(s))
        else:
            print(num2words(int(s)))
