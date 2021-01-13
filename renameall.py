#!/usr/bin/env python3
import sys, os, re, argparse

def renameall(patt, repl, dir=None, fixed=False, verbose=True, dryrun=False):
    if dir:
        os.chdir(dir)
    if fixed:
        patt = re.escape(patt)
    for file in os.listdir():
        if re.search(patt, file):
            new = re.sub(patt, repl, file)
            try:
                if not dryrun:
                    os.rename(file, new)
                if verbose or dryrun:
                    print("%s -> %s" % (file, new))
            except OSError as e:
                print('error:', e, file=sys.stderr)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('patt')
    p.add_argument('repl')
    p.add_argument('dir', nargs='?')
    p.add_argument('-F', '--fixed', action='store_true',
                   help='treat pattern as literal string')
    p.add_argument('-v', '--verbose', action='store_true', default=True,
                   help='print substitutions (default)')
    p.add_argument('-q', '--quiet', dest='verbose', action='store_false',
                   help='no output')
    p.add_argument('-d', '--dryrun', action='store_true',
                   help="print substitutions but don't rename files")
    args = p.parse_args()
    renameall(**vars(args))
