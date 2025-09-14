#!/usr/bin/env python3
import sys, os, re, math, argparse

def human_readable(n, prec=1, strip=True, decimal=False, ones='B'):
    base = 1000 if decimal else 1024
    power = min(max(int(math.log(abs(n), base)), 0), 6) if n else 0
    num = '{:.{}f}'.format(n / base**power, prec)
    if strip and '.' in num:
        num = num.rstrip('0').rstrip('.')
    return num + [ones, *'KMGTPE'][power]

def parse_human(s, decimal=False):
    base = 1000 if decimal else 1024
    s = s.strip().upper()
    m = re.fullmatch(r'(.*?)\s*([KMGTPE])?B?', s)
    power = ' KMGTPE'.index(m.group(2) or ' ')
    return round(float(m.group(1)) * base**power)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--parse', action='store_true')
    p.add_argument('-d', '--decimal', action='store_true')
    p.add_argument('-P', '--precision', type=int, default=1)
    p.add_argument('input', nargs='*')
    args = p.parse_args()
    if len(args.input) == 1 and os.path.exists(args.input[0]):
        nums = open(args.input[0])
    elif args.input and args.input != ['-']:
        nums = args.input
    else:
        nums = sys.stdin
    for n in nums:
        if args.parse:
            print(parse_human(n, args.decimal))
        else:
            print(human_readable(
                int(n), prec=args.precision, decimal=args.decimal))
