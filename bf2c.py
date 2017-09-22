#!/usr/bin/env python3
import sys

HEADER = '''\
#include <stdio.h>

unsigned char mem[0x10000];

int main(void) {
    unsigned char *ptr = mem;
    int chr;
'''
FOOTER = '''\
    return 0;
}
'''
GT = '''\
    ++ptr;
'''
LT = '''\
    --ptr;
'''
PLUS = '''\
    ++*ptr;
'''
MINUS = '''\
    --*ptr;
'''
DOT = '''\
    putchar(*ptr);
'''
COMMA = '''\
    *ptr = (chr = getchar()) != EOF ? chr : 0;
'''
LBRACKET = '''\
    while (*ptr) {
'''
RBRACKET = '''\
    }
'''

COMMANDS = {'>': GT, '<': LT, '+': PLUS, '-': MINUS, '.': DOT, ',': COMMA,
            '[': LBRACKET, ']': RBRACKET}

def bf2c(code):
    ccode = [HEADER]
    for c in code:
        comm = COMMANDS.get(c)
        if comm:
            ccode.append(comm)
    ccode.append(FOOTER)
    return ''.join(ccode)

if __name__ == '__main__':
    file = sys.stdin
    if len(sys.argv) >= 2 and sys.argv[1] != '-':
        file = open(sys.argv[1])
    code = file.read()
    ccode = bf2c(code)
    sys.stdout.write(ccode)
