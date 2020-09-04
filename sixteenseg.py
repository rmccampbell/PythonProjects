#!/usr/bin/env python3
import re
from itertools import zip_longest

PATTERN = r'''
 _ _  
|\|/| 
 - - .
|/|\| 
 - - .
'''[1:]

TEMPLATE = '''\
 0 1  
789A2 
 F B H
6EDC3 
 5 4 G
'''

PATTERN_A = r'''
 _  _   
|_\|_/|.
|_/|_\|.
'''[1:]

TEMPLATE_A = '''\
 0  1   
7F89BA2H
65ED4C3G
'''

ASCII_TABLE = [
#            !        "        #        $        %        &        '
    0x00000, 0x1000c, 0x00204, 0x0aa3c, 0x0aabb, 0x0ee99, 0x09371, 0x00200,
#   (        )        *        +        ,        -        .        /
    0x01400, 0x04100, 0x0ff00, 0x0aa00, 0x04000, 0x08800, 0x10000, 0x04400,
#   0        1        2        3        4        5        6        7
    0x044ff, 0x0040c, 0x08877, 0x0083f, 0x0888c, 0x090b3, 0x088fb, 0x0000f,
#   8        9        :        ;        <        =        >        ?
    0x088ff, 0x088bf, 0x30000, 0x0c000, 0x09400, 0x08830, 0x04900, 0x12807,
#   @        A        B        C        D        E        F        G
    0x00af7, 0x088cf, 0x02a3f, 0x000f3, 0x0223f, 0x080f3, 0x080c3, 0x008fb,
#   H        I        J        K        L        M        N        O
    0x088cc, 0x02233, 0x0007c, 0x094c0, 0x000f0, 0x005cc, 0x011cc, 0x000ff,
#   P        Q        R        S        T        U        V        W
    0x088c7, 0x010ff, 0x098c7, 0x088bb, 0x02203, 0x000fc, 0x044c0, 0x050cc,
#   X        Y        Z        [        \        ]        ^        _
    0x05500, 0x088bc, 0x04433, 0x02212, 0x01100, 0x02221, 0x05000, 0x00030,
#   `        a        b        c        d        e        f        g
    0x00100, 0x0a070, 0x0a0e0, 0x08060, 0x0a260, 0x0c060, 0x0aa02, 0x0a2a1,
#   h        i        j        k        l        m        n        o
    0x0a0c0, 0x02002, 0x02260, 0x03600, 0x02200, 0x0a848, 0x0a040, 0x0a060,
#   p        q        r        s        t        u        v        w
    0x082c1, 0x0a281, 0x08040, 0x0a0a1, 0x080e0, 0x02060, 0x04040, 0x05048,
#   x        y        z        {        |        }        ~
    0x05500, 0x00a1c, 0x0c020, 0x0a212, 0x02200, 0x02a21, 0x00A85, 0x00000,
]

ASCII_TABLE_A = ASCII_TABLE[:]
ASCII_TABLE_A[ord('!') - 0x20] = 0x10004

def ansi_len(s):
    return len(re.sub(r'\x1b\[.*?m', '', s))

def ansi_pad(s, w):
    return s + ' '*(w - ansi_len(s))

def hconcat(*strings):
    # Reverse lines so zip_longest pads at top instead of bottom
    line_lists = [s.splitlines()[::-1] for s in strings]
    widths = [max(map(ansi_len, lines)) for lines in line_lists]
    return '\n'.join(
        ''.join(ansi_pad(line, w) for line, w in zip(row, widths))
        for row in reversed(list(zip_longest(*line_lists, fillvalue='')))
    )

def decode(x, ansi=True):
    if hasattr(x, '__iter__') and not isinstance(x, str):
        return hconcat(*(decode(y, ansi) for y in x))
    pattern, template = (PATTERN_A, TEMPLATE_A) if ansi else (PATTERN, TEMPLATE)
    s = ''.join(
        c if (not d.isalnum()) or (x >> int(d, 18) & 1) else
        '' if ansi and c == '_' else ' '
        for c, d in zip(pattern, template)
    )
    if ansi:
        s = re.sub(r'_(.)', '\x1b[4m\\1\x1b[24m', s)
    return s

def sixteenseg(s, ansi=True):
    table = ASCII_TABLE_A if ansi else ASCII_TABLE
    rows = []
    for line in s.splitlines():
        row = []
        for c in re.findall(r'(?=[ -\x7f])[^.:!?][.:]|.', line):
            # Pass through non-ascii characters
            if not ' ' <= c[0] <= '\x7f':
                row.append(c)
                continue
            code = table[ord(c[0]) - 0x20]
            # Combine . and : with previous character
            if len(c) == 2:
                code |= table[ord(c[1]) - 0x20]
            row.append(decode(code, ansi))
        rows.append(hconcat(*row))
    return '\n'.join(rows)


if __name__ == '__main__':
    import sys, argparse
    p = argparse.ArgumentParser()
    p.add_argument('-A', '--no-ansi', dest='ansi', action='store_false')
    p.add_argument('text', nargs='*')
    args = p.parse_args()
    if args.text:
        for arg in args.text:
            print(sixteenseg(arg, args.ansi))
    else:
        for line in sys.stdin:
            print(sixteenseg(line.rstrip('\n'), args.ansi))
