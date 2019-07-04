#!/usr/bin/env python3
import sys
if __name__ == '__main__':
    content = sys.stdin.buffer.read()
    file = sys.stdout.buffer
    if len(sys.argv) > 1 and sys.argv[1] != '-':
        file = open(sys.argv[1], 'wb')
    try:
        file.write(content)
    except BrokenPipeError:
        pass
