#!/usr/bin/env python3
import sys
sys.stdout.buffer.write(sys.stdin.buffer.read().rstrip(b'\n\r'))
