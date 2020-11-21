#!/usr/bin/env python3
import sys, os, re, glob, argparse

def do_rename(old, new, verbose, dryrun):
    try:
        if not dryrun:
            os.rename(old, new)
        if verbose or dryrun:
            print('%s -> %s' % (old, new))
    except OSError as e:
        print('error:', e, file=sys.stderr)

def incfiles(pattern, start=None, end=None, inc=1, cyclic=False, verbose=True,
             dryrun=False):
    if start is None:
        start = 0
        while not os.path.exists(pattern % start):
            start += 1
            if start >= 100:
                raise ValueError("couldn't find file matching pattern between 0-99")
    if end is None:
        stop = start
        while os.path.exists(pattern % stop):
            stop += 1
    else:
        stop = end + 1
    if cyclic:
        n = stop - start
        # limit inc to interval [-n/2, n/2)
        inc = (inc + n//2) % n - n//2
    rng = range(start, stop)
    if inc > 0:
        rng = rng[::-1]
    for i in rng:
        j = i + inc        
        old = pattern % i
        if cyclic and not start <= j < stop:
            j = (j - start) % (stop - start) + start
            new = '_TEMP_' + pattern % j
        else:
            new = pattern % j
        do_rename(old, new, verbose, dryrun)
    if cyclic:
        rng = range(start, start + inc) if inc >= 0 else range(stop + inc, stop)
        for i in rng:
            old = '_TEMP_' + pattern % i
            new = pattern % i
            do_rename(old, new, verbose, dryrun)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('pattern')
    p.add_argument('start', nargs='?', type=int)
    p.add_argument('end', nargs='?', type=int)
    p.add_argument('-i', '--inc', type=int, default=1,
                   help='increment by INC (default: %(default)s)')
    p.add_argument('-c', '--cyclic', action='store_true', help='wrap arround')
    p.add_argument('-v', '--verbose', action='store_true', default=True,
                   help='print substitutions (default)')
    p.add_argument('-q', '--quiet', dest='verbose', action='store_false',
                   help='no output')
    p.add_argument('-d', '--dryrun', action='store_true',
                   help="print substitutions but don't rename files")
    args = p.parse_args()
    try:
        incfiles(**vars(args))
    except Exception as e:
        print('error:', e, file=sys.stderr)
