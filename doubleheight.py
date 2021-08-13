#!/usr/bin/env python3
"""Prints text in double width/height on terminals with DECDHL support (e.g. mintty)"""

import sys

if __name__ == '__main__':
    if sys.argv[1:]:
        lines = ' '.join(sys.argv[1:]).splitlines()
    else:
        lines = sys.stdin
    for l in lines:
        l = l.rstrip('\n')
        print('\x1b#3' + l)
        print('\x1b#4' + l)
