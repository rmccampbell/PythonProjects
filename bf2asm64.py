#!/usr/bin/env python3
import sys

HEADER = '''\
	.bss
mem:
	.space 0x10000
	.text
	.globl	main
main:
	pushq	%rbx
	subq	$32, %rsp
	leaq	mem(%rip), %rbx
'''
FOOTER = '''\
	xorl	%eax, %eax
	addq	$32, %rsp
	popq	%rbx
	ret
'''
GT = '''\
	addq	$1, %rbx
'''
LT = '''\
	subq	$1, %rbx
'''
PLUS = '''\
	addb	$1, (%rbx)
'''
MINUS = '''\
	subb	$1, (%rbx)
'''
DOT = '''\
	movzbl	(%rbx), %ecx
	call	putchar
'''
COMMA = '''\
	call	getchar
	movl	$0, %ecx
	cmpl	$-1, %eax
	cmove	%ecx, %eax
	movb	%al, (%rbx)
'''
LBRACKET = '''\
	movb	(%rbx), %al
	testb	%al, %al
	jz	.END{lbl}
.BEGIN{lbl}:
'''
RBRACKET = '''\
	movb	(%rbx), %al
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
