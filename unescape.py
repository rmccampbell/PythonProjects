#!/usr/bin/env python3
import sys, argparse

p = argparse.ArgumentParser()
p.add_argument('args', nargs='*')
p.add_argument('-b', '--binary', action='store_true')
p.add_argument('-u', '--utf8', action='store_true')
args = p.parse_args()

inpt = ' '.join(args.args)
unescaped = inpt.encode('latin-1', 'backslashreplace').decode('unicode_escape')
if args.binary:
    sys.stdout.buffer.write(unescaped.encode('latin-1'))
elif args.utf8:
    sys.stdout.buffer.write(unescaped.encode('utf-8'))
else:
    sys.stdout.write(unescaped)
