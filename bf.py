#!/usr/bin/env python3
import sys, argparse, io

def run(code, debug=False, text=False, eof_nochange=False):
    code = [c for c in code if c in '><+-.,[]dpi']
    array = [0] * 30000
    p = 0
    i = 0
    nl = None if text else '\n'
    if text:
        stdin, stdout = sys.stdin, sys.stdout
        _chr = chr
    else:
        stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
        _chr = lambda i: chr(i).encode('latin-1')
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
            stdout.write(_chr(array[p]))
        elif c == ',':
            b = stdin.read(1)
            if b or not eof_nochange:
                array[p] = ord(b) & 0xff if b else 0
        elif c == '[':
            if not array[p]:
                level = 1
                while level:
                    i += 1
                    if code[i] == '[':
                        level += 1
                    elif code[i] == ']':
                        level -= 1
        elif c == ']':
            if array[p]:
                level = 1
                while level:
                    i -= 1
                    if code[i] == '[':
                        level -= 1
                    elif code[i] == ']':
                        level += 1
        elif c == 'd' and debug:
            print(p, array[:20])
        elif c == 'p' and debug:
            print(array[p])
        elif c == 'i' and debug:
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
    run(code, args.debug, args.text, args.eof_nochange)
