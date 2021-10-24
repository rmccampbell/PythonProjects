#!/usr/bin/env python3
import sys, os, argparse, ctypes
import os.path as osp

def pathv(add=None, index=None, remove=None, contains=None, lines=False,
          evalable=False):
    value = os.environ['PATH']
    values = value.split(os.pathsep)
    if contains:
        if not isinstance(contains, (list, tuple)):
            contains = [contains]
        values = {osp.normcase(osp.normpath(osp.expandvars(val)))
                  for val in values}
        for path in contains:
            if osp.normcase(osp.abspath(path)) in values:
                print('"%s" in path' % path)
            else:
                print('"%s" not in path' % path)
        return
    if remove is not None:
        if remove not in values:
            raise ValueError('"%s" not in path' % remove)
        values.remove(remove)
    if add is not None:
        if add in values:
            raise ValueError('"%s" already in path' % add)
        if index is None:
            index = len(values)
        values.insert(index, add)
    if add is not None or remove is not None:
        value = os.pathsep.join(values)
    if lines:
        print(value.replace(os.pathsep, '\n'))
    elif evalable:
        print('PATH=' + value)
    else:
        print(value)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add')
    parser.add_argument('-i', '--index', type=int)
    parser.add_argument('-r', '--remove')
    parser.add_argument('-c', '--contains', nargs='+')
    parser.add_argument('-l', '--lines', action='store_true')
    parser.add_argument('-e', '--evalable', action='store_true')
    args = parser.parse_args()
    try:
        pathv(**vars(args))
    except Exception as e:
        sys.exit(e)
