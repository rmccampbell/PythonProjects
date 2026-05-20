#!/usr/bin/env python3
'''Use OSC 8 to create hyperlinks in a terminal'''

def linkify(url, text=None):
    return f'\x1b]8;;{url}\x1b\\{text or url}\x1b]8;;\x1b\\'

if __name__ == '__main__':
    import sys
    print(linkify(*sys.argv[1:]))
