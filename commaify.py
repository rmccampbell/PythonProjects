#!/usr/bin/env python3

import sys

if __name__ == '__main__':
    for s in sys.argv[1:] or sys.stdin:
        print(f'{int(s):,}')
