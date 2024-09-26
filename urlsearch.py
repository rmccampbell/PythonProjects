#!/usr/bin/env python3
import argparse, sys, re
from urllib.request import urlopen

def urlsearch(url, phrase, start=1, end=sys.maxsize, verbose=False, 
              print_match=False, case_sensitive=False, ignore_errors=False):
    step = 1 if start <= end else -1
    for i in range(start, end+step, step):
        urli = url.format(i)
        try:
            text = urlopen(urli).read()
            text = text.decode('utf-8', 'ignore').replace('\r\n', '\n')
        except OSError:
            if not ignore_errors:
                print('error: {} not found'.format(urli), file=sys.stderr)
            continue
        flags = 0 if case_sensitive else re.IGNORECASE
        match = re.search(phrase, text, flags)
        if match:
            s = '*{}*'.format(urli) if verbose else urli
            if print_match:
                s += ': ' + match.group()
            print(s)
        elif verbose:
            print(urli)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('phrase')
    p.add_argument('start', type=int, nargs='?', default=0, help='default: %(default)s')
    p.add_argument('end', type=int, nargs='?', default=sys.maxsize)
    p.add_argument('-c', '--case-sensitive', action='store_true')
    p.add_argument('-m', '--print-match', action='store_true')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('-i', '--ignore-errors', action='store_true')
    args = p.parse_args()
    try:
        urlsearch(**vars(args))
    except KeyboardInterrupt:
        pass
