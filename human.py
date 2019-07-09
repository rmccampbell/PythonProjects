#!/usr/bin/env python3
import sys, os

def human_readable(n, prec=1, strip=True):
    power = min(max((int(n).bit_length() - 1) // 10, 0), 6)
    num = '{:.{}f}'.format(n / 1024**power, prec)
    if strip and '.' in num:
        num = num.rstrip('0').rstrip('.')
    return num + 'BKMGTPE'[power]

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] != '-':
        if os.path.exists(sys.argv[1]):
            nums = open(sys.argv[1])
        else:
            nums = sys.argv[1:]
    else:
        nums = sys.stdin
    for n in nums:
        print(human_readable(int(n)))
