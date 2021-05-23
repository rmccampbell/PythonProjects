#!/usr/bin/env python3
import sys

HEADER = '''\
#ifdef __x86_64__
	#define XSP %rsp
	#define XBX %rbx
	#if defined(_WIN64) || defined(__CYGWIN__)
		#define PARAM %ecx
	#else
		#define PARAM %edi
	#endif
#else
	#define XSP %esp
	#define XBX %ebx
	#define PARAM %eax
#endif

	.bss
mem:
	.zero	0x10000

	.text
	.globl	main
main:
	push	XBX
	sub	$32, XSP
#ifdef __x86_64__
	leaq	mem(%rip), XBX
#else
	movl	$mem, XBX
#endif
'''

FOOTER = '''\
	xorl	%eax, %eax
	add	$32, XSP
	pop	XBX
	ret
'''

GT = '''\
	add	$1, XBX
'''

LT = '''\
	sub	$1, XBX
'''

PLUS = '''\
	addb	$1, (XBX)
'''

MINUS = '''\
	subb	$1, (XBX)
'''

DOT = '''\
	movzbl	(XBX), PARAM
#ifdef __i386__
	movl	PARAM, (%esp)
#endif
	call	putchar
'''

COMMA = '''\
	call	getchar
	movl	$0, %ecx
	cmpl	$-1, %eax
	cmove	%ecx, %eax
	movb	%al, (XBX)
'''

LBRACKET = '''\
	movb	(XBX), %al
	testb	%al, %al
	jz	.END{lbl}
.BEGIN{lbl}:
'''

RBRACKET = '''\
	movb	(XBX), %al
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
