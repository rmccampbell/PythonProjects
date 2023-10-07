#!/usr/bin/python3 -u
import sys

for n in sys.argv[1:] or sys.stdin:
	sys.stdout.buffer.write(bytes([int(n)]))
