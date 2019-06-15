#!/usr/bin/env python3
import sys
import argparse
import termcolor

def dash_none(x):
    return x if x != '-' else None

if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            import winansi
            winansi.enable()
        except:
            pass

    p = argparse.ArgumentParser()
    p.add_argument('color', nargs='?', type=dash_none)
    p.add_argument('bgcolor', nargs='?', type=dash_none)
    for char, attr in [('b', 'bold'), ('d', 'dark'), ('u', 'underline'), 
                       ('k', 'blink'), ('r', 'reverse'), ('c', 'concealed')]:
        p.add_argument('-' + char, '--' + attr, const=attr, dest='attrs',
                       action='append_const')
    args = p.parse_args()

    if not (args.color or args.bgcolor or args.attrs):
        args.color = 'red'
    if args.bgcolor and not args.bgcolor.startswith('on_'):
        args.bgcolor = 'on_' + args.bgcolor

    escapes = termcolor.colored('', args.color, args.bgcolor, args.attrs)
    start = escapes[:-len(termcolor.RESET)]

    sys.stdout.write(start)
    sys.stdout.writelines(sys.stdin)
    sys.stdout.write(termcolor.RESET)
