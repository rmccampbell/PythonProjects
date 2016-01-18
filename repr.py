#!/usr/bin/env python3
import sys

file = sys.stdin.buffer
if len(sys.argv) > 1:
    file = open(sys.argv[1], 'rb')
print(repr(file.read())[1:])
