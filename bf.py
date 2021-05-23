#!/usr/bin/env python3
import sys, argparse, io

MEMSIZE = 0x10000

def run(source, debug=False, newline_conv=False, eof_nochange=False):
    commands = set('><+-.,[]' + ('dDpi' if debug else ''))
    code = []
    brackets = []
    for c in source:
        if c in commands:
            code.append(c)
            if c == '[':
                brackets.append(len(code))
                code.append(-1)
            elif c == ']':
                match = brackets.pop()
                code[match] = len(code)
                code.append(match)

    array = [0] * MEMSIZE
    p = 0
    i = 0
    if newline_conv:
        stdin = io.TextIOWrapper(sys.stdin.buffer, 'latin-1')
        stdout = io.TextIOWrapper(sys.stdout.buffer.raw, 'latin-1',
                                  write_through=True)
        chr_ = chr
    else:
        stdin, stdout = sys.stdin.buffer, sys.stdout.buffer.raw
        chr_ = lambda i: bytes([i])
    while i < len(code):
        c = code[i]
        if c == '>':
            p += 1
        elif c == '<':
            p -= 1
        elif c == '+':
            array[p] = (array[p] + 1) & 0xff
        elif c == '-':
            array[p] = (array[p] - 1) & 0xff
        elif c == '.':
            stdout.write(chr_(array[p]))
            # stdout.flush()
        elif c == ',':
            b = stdin.read(1)
            if b or not eof_nochange:
                array[p] = ord(b) & 0xff if b else 0
        elif c == '[':
            i += 1
            if not array[p]:
                i = code[i]
        elif c == ']':
            i += 1
            if array[p]:
                i = code[i]
        elif debug:
            if c in ('d', 'D'):
                end = next((i for i in range(256)[::-1] if array[i]), 0)
                x = array[p]
                array[p] = Highlighter(x)
                print(p, array[:max(end+1, 20)])
                array[p] = x
                if c == 'D':
                    input()
            elif c == 'p':
                print(array[p])
            elif c == 'i':
                array[p] = int(input()) & 0xff
        i += 1

class Highlighter:
    def __init__(self, x):
        self.x = x
    def __repr__(self):
        return '\x1b[7m%r\x1b[0m' % self.x

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-d', '--debug', action='store_true')
    p.add_argument('-n', '--newline-conv', action='store_true')
    p.add_argument('-e', '--eof-nochange', action='store_true')
    p.add_argument('-c', '--cmd')
    p.add_argument('file', nargs='?', type=argparse.FileType(), default='-')
    args = p.parse_args()
    code = args.cmd or args.file.read()
    try:
        run(code, args.debug, args.newline_conv, args.eof_nochange)
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    except OSError as e:
        # Broken pipe
        if e.errno != 22:
            raise
