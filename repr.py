#!/usr/bin/env python3
import sys

unicode = False
if '-u' in sys.argv:
    unicode = True
    sys.argv.remove('-u')

if len(sys.argv) > 1:
    mode = 'r' if unicode else 'rb'
    encoding = 'utf-8' if unicode else None
    file = open(sys.argv[1], mode, encoding=encoding)
else:
    file = sys.stdin if unicode else sys.stdin.buffer

print(ascii(file.read()).lstrip('b'))
