#!/usr/bin/env python3
import sys
import argparse
import colors

RESET = '\x1b[0m'

def dash_none(x):
    return x if x != '-' else None

if __name__ == '__main__':
##    if sys.platform == 'win32':
##        try:
##            import winansi
##            winansi.enable()
##        except:
##            pass

    p = argparse.ArgumentParser()
    p.add_argument('fgcolor', nargs='?', type=dash_none)
    p.add_argument('bgcolor', nargs='?', type=dash_none)
    p.add_argument('-m', '--message')
    for char, flag, style in [
        ('b', 'bold', 'bold'),           ('f', 'faint', 'faint'),
        ('i', 'italic', 'italic'),       ('u', 'underline', 'underline'),
        ('k', 'blink', 'blink'),         ('r', 'reverse', 'negative'),
        ('c', 'concealed', 'concealed'), ('s', 'strikethrough', 'crossed'),
    ]:
        p.add_argument('-' + char, '--' + flag, const=style, dest='styles',
                       action='append_const')
    args = p.parse_args()

    if not (args.fgcolor or args.bgcolor or args.styles):
        args.fgcolor = 'red'
    style = '+'.join(args.styles or [])

    if args.message:
        print(colors.color(args.message, args.fgcolor, args.bgcolor, style))
    else:
        escapes = colors.color('', args.fgcolor, args.bgcolor, style)
        sys.stdout.write(escapes[:-len(RESET)])
        sys.stdout.writelines(sys.stdin)
        sys.stdout.write(RESET)
