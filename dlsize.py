#!/usr/bin/env python3
import sys, argparse
from urllib.request import Request, urlopen

def dlsize(url):
    req = Request(url, method='HEAD')
    with urlopen(req) as resp:
        return int(resp.headers.get('Content-Length', -1))

def human_readable(n, prec=1, strip=True):
    power = max((int(n).bit_length() - 1) // 10, 0)
    num = '{:.{}f}'.format(n / 1024**power, prec)
    if strip and '.' in num:
        num = num.rstrip('0').rstrip('.')
    return num + 'BKMGTPE'[power]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-b', '--bytes', action='store_true')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('urls', nargs='*')
    args = p.parse_args()
    urls = args.urls or (l.strip() for l in sys.stdin)
    for url in urls:
        if args.verbose:
            print(url)
        s = dlsize(url)
        if s < 0:
            print('Unknown size')
        elif args.bytes:
            print(s)
        else:
            print(human_readable(s))
