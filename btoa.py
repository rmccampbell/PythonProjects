#!/usr/bin/python3
import sys

while b := sys.stdin.buffer.read(1):
	print(ord(b))
