#!/usr/bin/env python3
from itertools import zip_longest

def ssplit(s, *inds):
    prev = 0
    for ind in inds:
        yield s[prev:ind]
        prev = ind
    yield s[prev:]

def hsplit(string, *inds):
    return list(map('\n'.join,
                    zip(*(ssplit(s, *inds) for s in string.splitlines()))))

DIGS = '''\
 _     _  _     _  _  _  _  _  _     _     _  _ 
| |  | _| _||_||_ |_   ||_||_||_||_ |   _||_ |_ 
|_|  ||_  _|  | _||_|  ||_| _|| ||_||_ |_||_ |
'''

DIGS = hsplit(DIGS, *range(3, 3*16, 3))

PATTERN = '''\
 _ 
|_|
|_|
'''

TEMPLATE = '''\
 0 
561
432
'''

def hconcat(*strings):
    line_lists = [s.splitlines() for s in strings]
    widths = [max(map(len, lines)) for lines in line_lists]
    return '\n'.join(
        ''.join(line.ljust(w) for line, w in zip(row, widths))
        for row in zip_longest(*line_lists, fillvalue='')
    )

def decode(x):
    if hasattr(x, '__iter__') and not isinstance(x, str):
        return hconcat(*(decode(y) for y in x))
    return ''.join(
        c if (not d.isdigit()) or (x >> int(d) & 1) else ' '
        for c, d in zip(PATTERN, TEMPLATE)
    )

def sevenseg_char(c):
    if c == ' ':
        return '\n'.join('   ')
    if c == ':':
        return '\n'.join(' ..')
    if c == '.':
        return '\n'.join('  .')
    return DIGS[int(c, 16)]

def sevenseg_str(s):
    return hconcat(*map(sevenseg_char, s))

def sevenseg_num(n, hex=False):
    return sevenseg_str(format(n, 'x' if hex else 'd'))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            print(sevenseg_str(arg))
    else:
        for line in sys.stdin:
            print(sevenseg_str(line.rstrip('\n')))
