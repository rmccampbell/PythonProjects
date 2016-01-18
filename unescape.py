#!/usr/bin/env python3
import sys

binary = False
if len(sys.argv) > 1 and sys.argv[1] == '-b':
    binary = True
    del sys.argv[1]
inpt = ' '.join(sys.argv[1:])
unescaped = inpt.encode('latin-1', 'backslashreplace').decode('unicode_escape')
if binary:
    sys.stdout.buffer.write(unescaped.encode('latin-1'))
else:
    sys.stdout.write(unescaped)
