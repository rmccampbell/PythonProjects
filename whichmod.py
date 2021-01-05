#!/usr/bin/env python3

import sys, importlib

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
        sys.exit('usage: {} module'.format(sys.argv[0]))
    name = sys.argv[1]
    mod = importlib.import_module(name)
    try:
        print(mod.__file__)
    except AttributeError:
        try:
            for path in mod.__path__:
                print(path)
        except AttributeError:
            if name in sys.builtin_module_names:
                print('<built-in>')
            else:
                print('<unknown>')
