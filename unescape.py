#!/usr/bin/env python3
import sys, argparse

p = argparse.ArgumentParser()
p.add_argument('input', nargs='*')
p.add_argument('-b', '--binary', action='store_true')
p.add_argument('-u', '--utf8', action='store_true')
p.add_argument('-n', '--nonewline', action='store_true')
args = p.parse_args()

for inpt in args.input:
    unescaped = inpt.encode('latin-1', 'backslashreplace').decode('unicode_escape')
    if args.binary:
        sys.stdout.buffer.write(unescaped.encode('latin-1'))
    elif args.utf8:
        sys.stdout.buffer.write(unescaped.encode('utf-8'))
    else:
        sys.stdout.write(unescaped)

    if not args.binary or args.nonewline:
        print(flush=True)
