#!/usr/bin/env python3
import os, base64

def tmux_dcs(s):
    escaped = s.replace('\x1b', '\x1b\x1b')
    return f'\x1bPtmux;{escaped}\x1b\\'

def osc52(s):
    if isinstance(s, str):
        s = s.encode()
    encoded = base64.b64encode(s).decode()
    return f'\x1b]52;c;{encoded}\a'

def osc52_copy(s):
    esc = osc52(s)
    term = os.environ['TERM']
    if term.startswith('screen') or term.startswith('tmux'):
        esc = tmux_dcs(esc)
    print(esc, end='', flush=True)


if __name__ == '__main__':
    import sys
    data = ' '.join(sys.argv[1:]) or sys.stdin.read().rstrip('\n')
    osc52_copy(data)
