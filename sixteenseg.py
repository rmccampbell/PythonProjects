#!/usr/bin/env python3
from itertools import zip_longest

PATTERN = r'''
 _ _ 
|\|/|
 - - 
|/|\|
 - - .
'''[1:]

TEMPLATE = '''\
 0 1 
789A2
 F B 
6EDC3
 5 4 G
'''

ASCII_TABLE = [
#            !        "        #        $        %        &        '
    0x00000, 0x1000c, 0x00204, 0x0aa3c, 0x0aabb, 0x0ee99, 0x09371, 0x00200,
#   (        )        *        +        ,        -        .        /
    0x01400, 0x04100, 0x0ff00, 0x0aa00, 0x04000, 0x08800, 0x10000, 0x04400,
#   0        1        2        3        4        5        6        7
    0x044ff, 0x0040c, 0x08877, 0x0083f, 0x0888c, 0x090b3, 0x088fb, 0x0000f,
#   8        9        :        ;        <        =        >        ?
    0x088ff, 0x088bf, 0x02200, 0x04200, 0x09400, 0x08830, 0x04900, 0x12807,
#   @        A        B        C        D        E        F        G
    0x00af7, 0x088cf, 0x02a3f, 0x000f3, 0x0223f, 0x080f3, 0x080c3, 0x008fb,
#   H        I        J        K        L        M        N        O
    0x088cc, 0x02233, 0x0007c, 0x094c0, 0x000f0, 0x005cc, 0x011cc, 0x000ff,
#   P        Q        R        S        T        U        V        W
    0x088c7, 0x010ff, 0x098c7, 0x088bb, 0x02203, 0x000fc, 0x044c0, 0x050cc,
#   X        Y        Z        [        \        ]        ^        _
    0x05500, 0x088bc, 0x04433, 0x02212, 0x01100, 0x02221, 0x05000, 0x00030,
#   `        a        b        c        d        e        f        g
    0x00100, 0x0a070, 0x0a0e0, 0x08060, 0x0281c, 0x0c060, 0x0aa02, 0x0a2a1,
#   h        i        j        k        l        m        n        o
    0x0a0c0, 0x02400, 0x02260, 0x03600, 0x000c0, 0x0a848, 0x0a040, 0x0a060,
#   p        q        r        s        t        u        v        w
    0x082c1, 0x0a281, 0x08040, 0x0a0a1, 0x080e0, 0x02060, 0x04040, 0x05048,
#   x        y        z        {        |        }        ~
    0x05500, 0x00a1c, 0x0c020, 0x0a212, 0x02200, 0x02a21, 0x08844, 0x00000,
]

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
        c if (not d.isalnum()) or (x >> int(d, 17) & 1) else ' '
        for c, d in zip(PATTERN, TEMPLATE)
    )

def sixteenseg(s):
    if len(s) > 1:
        return '\n'.join(hconcat(*map(sixteenseg, l)) for l in s.splitlines())
    return decode(ASCII_TABLE[ord(s) - 0x20]) if ' ' <= s <= '\x7f' else s


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            print(sixteenseg(arg))
    else:
        for line in sys.stdin:
            print(sixteenseg(line.rstrip('\n')))
