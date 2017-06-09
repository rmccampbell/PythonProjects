#!/usr/bin/python3 -u
import sys, argparse, io

MEMSIZE = 30000

def run(code, debug=False, text=False, eof_nochange=False):
    code = [c for c in code if c in '><+-.,[]' + ('dpi' if debug else '')]
    array = [0] * MEMSIZE
    p = 0
    i = 0
    if text:
        stdin, stdout = sys.stdin, sys.stdout
        chr_ = chr
    else:
        stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
        def chr_(i): return chr(i).encode('latin-1')
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
            try:
                stdout.write(chr_(array[p]))
            except OSError:
                break
        elif c == ',':
            b = stdin.read(1)
            if b or not eof_nochange:
                array[p] = ord(b) & 0xff if b else 0
        elif c == '[':
            if not array[p]:
                depth = 1
                while depth:
                    i += 1
                    c = code[i]
                    if c == '[':
                        depth += 1
                    elif c == ']':
                        depth -= 1
        elif c == ']':
            if array[p]:
                depth = 1
                while depth:
                    i -= 1
                    c = code[i]
                    if c == '[':
                        depth -= 1
                    elif c == ']':
                        depth += 1
        elif debug:
            if c == 'd':
                end = next((i for i in range(MEMSIZE-1, -1, -1) if array[i]), 0)
                print(p, array[:max(end+1, 20)])
            elif c == 'p':
                print(array[p])
            elif c == 'i':
                array[p] = int(input()) & 0xff
        i += 1

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-d', '--debug', action='store_true')
    p.add_argument('-t', '--text', action='store_true')
    p.add_argument('-e', '--eof-nochange', action='store_true')
    p.add_argument('-c', '--cmd')
    p.add_argument('file', nargs='?', type=argparse.FileType(), default='-')
    args = p.parse_args()
    code = args.cmd or args.file.read()
    try:
        run(code, args.debug, args.text, args.eof_nochange)
    except KeyboardInterrupt:
        pass
