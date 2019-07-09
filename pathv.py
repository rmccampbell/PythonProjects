#!/usr/bin/env python3
import sys, os, argparse, ctypes
import os.path as op

def main(add=None, index=None, remove=None, contains=(), lines=False):
    value = os.environ['PATH']
    values = value.split(os.pathsep)
    if contains:
        values = {op.normcase(op.normpath(op.expandvars(val)))
                  for val in values}
        for path in contains:
            if op.normcase(op.abspath(path)) in values:
                print('"%s" in path' % path)
            else:
                print('"%s" not in path' % path)
        return
    if remove is not None:
        if remove not in values:
            print('"%s" not in path' % remove, file=sys.stderr)
            sys.exit(1)
        values.remove(remove)
    if add is not None:
        if add in values:
            print('"%s" already in path' % add, file=sys.stderr)
            sys.exit(1)
        if index is None:
            index = len(values)
        values.insert(index, add)
    if add is not None or remove is not None:
        value = os.pathsep.join(values)
    if lines:
        print(value.replace(os.pathsep, '\n'))
    else:
        print('PATH=' + value)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add')
    parser.add_argument('-i', '--index', type=int)
    parser.add_argument('-r', '--remove')
    parser.add_argument('-c', '--contains', default=[], action='append')
    parser.add_argument('-l', '--lines', action='store_true')
    args = parser.parse_args()
    main(**vars(args))
