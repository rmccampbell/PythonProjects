#!/usr/bin/env python3
import sys, argparse

def print_table(arr, pad=2):
    widths = [max(len(r[i]) for r in arr if i < len(r))
              for i in range(max(map(len, arr)))]
    enc = sys.stdout.encoding
    for r in arr:
        l = (' '*pad).join(s.ljust(widths[i]) for i, s in enumerate(r))
        print(l.encode(enc, 'replace').decode(enc))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('file', nargs='?', type=argparse.FileType('r'), default='-')
    p.add_argument('-p', '--pad', type=int, default=2,
                   help='default: %(default)s')
    p.add_argument('-d', '--delim', default='\t',
                   help='default: %(default)r')
    args = p.parse_args()
    table = [l.rstrip().split(args.delim) for l in args.file]
    print_table(table, args.pad)
