from itertools import zip_longest

def sbreak(s, *inds):
    prev = 0
    for ind in inds:
        yield s[prev:ind]
        prev = ind
    yield s[prev:]

def hsplit(string, *inds):
    return list(map('\n'.join,
                    zip(*(sbreak(s, *inds) for s in string.splitlines()))))

_digs = '''\
 _     _  _     _  _  _  _  _  _     _     _  _ 
| |  | _| _||_||_ |_   ||_||_||_||_ |   _||_ |_ 
|_|  ||_  _|  | _||_|  ||_| _|| ||_||_ |_||_ |  '''

DIGS = hsplit(_digs, *range(3, 3*16, 3))

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

def decode(n):
    return ''.join(
        c if (not d.isdigit()) or (n >> int(d) & 1) else ' '
        for c, d in zip(PATTERN, TEMPLATE)
    )

def char_to_7seg(c):
    if c == ' ':
        return '\n'.join('   ')
    if c == ':':
        return '\n'.join(' ..')
    if c == '.':
        return '\n'.join('  .')
    return DIGS[int(c, 16)]

def str_to_7seg(s):
    return hconcat(*map(char_to_7seg, s))

def num_to_7seg(n, hex=False):
    return str_to_7seg(format(n, 'x' if hex else 'd'))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            print(str_to_7seg(arg))
    else:
        for line in sys.stdin:
            print(str_to_7seg(line.rstrip('\n')))
