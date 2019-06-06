#!/usr/bin/env python3
import sys

HEADER = '''\
	.bss
mem:
	.space 0x10000
	.text
	.globl	_main
_main:
	pushl	%ebx
	subl	$4, %esp
	movl	$mem, %ebx
'''
FOOTER = '''\
	xorl	%eax, %eax
	addl	$4, %esp
	popl	%ebx
	ret
'''
GT = '''\
	addl	$1, %ebx
'''
LT = '''\
	subl	$1, %ebx
'''
PLUS = '''\
	addb	$1, (%ebx)
'''
MINUS = '''\
	subb	$1, (%ebx)
'''
DOT = '''\
	movzbl	(%ebx), %eax
	movl	%eax, (%esp)
	call	_putchar
'''
COMMA = '''\
	call	_getchar
	movl	$0, %ecx
	cmpl	$-1, %eax
	cmove	%ecx, %eax
	movb	%al, (%ebx)
'''
LBRACKET = '''\
	movb	(%ebx), %al
	testb	%al, %al
	jz	.END{lbl}
.BEGIN{lbl}:
'''
RBRACKET = '''\
	movb	(%ebx), %al
	testb	%al, %al
	jnz	.BEGIN{lbl}
.END{lbl}:
'''

COMMANDS = {'>': GT, '<': LT, '+': PLUS, '-': MINUS, '.': DOT, ',': COMMA,
            '[': LBRACKET, ']': RBRACKET}

def bf2asm(code):
    asm = [HEADER]
    brackets = []
    bracketi = 0
    for c in code:
        comm = COMMANDS.get(c)
        if comm is None:
            continue
        if c == '[':
            comm = comm.format(lbl=bracketi)
            brackets.append(bracketi)
            bracketi += 1
        elif c == ']':
            bracketj = brackets.pop()
            comm = comm.format(lbl=bracketj)
        asm.append(comm)
    asm.append(FOOTER)
    return ''.join(asm)

if __name__ == '__main__':
    file = sys.stdin
    if len(sys.argv) >= 2 and sys.argv[1] != '-':
        file = open(sys.argv[1])
    code = file.read()
    asm = bf2asm(code)
    sys.stdout.write(asm)
