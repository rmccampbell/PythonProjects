#!/usr/bin/env python3
import sys, os

byte = len(sys.argv) > 1 and sys.argv[1] == '-b'
if byte:
    sys.argv.remove('-b')

for arg in sys.argv[1:]:
    if byte:
        print(repr(os.fsencode(arg)).lstrip('b'))
    else:
        print(repr(arg))
