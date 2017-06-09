#!/usr/bin/env python3
import sys
import socket

NOP = 0
WRT = 1
RD  = 2
IF  = 3
EIF = 4
FWD = 5
BAK = 6
INC = 7
DEC = 8
CON = 9
END = 10

opmap = ['NOP', 'WRT', 'RD', 'IF', 'EIF', 'FWD', 'BAK', 'INC', 'DEC', 'CON',
         'END']


def dis(code, prnt=True):
    words = code.split()
    ops = (sum(map(int, filter(str.isdigit, w))) for w in words)
    ret = []
    for op in ops:
        line = opmap[op] if op <= 10 else '<%#04x>' % op
        if op in (FWD, BAK, INC, DEC):
            line += ' %#04x' % next(ops)
        ret.append(line)
    if prnt:
        print('\n'.join(ret))
    else:
        return ret


def run(code):
    words = code.split()
    ops = [sum(map(int, filter(str.isdigit, s))) for s in words]

    memory = [0] * 0x10000
    ip = 0
    mp = len(ops)
    memory[:mp] = ops

    sock = None
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        op = memory[ip]
        if op == END:
            break
        elif op == WRT:
            stdout.write(chr(memory[mp]).encode('latin-1'))
        elif op == RD:
            memory[mp] = ord(stdin.read(1) or '\0')
        elif op == IF:
            if not memory[mp]:
                depth = 1
                while depth:
                    ip = (ip + 1) & 0xffff
                    if memory[ip] == IF:
                        depth += 1
                    elif memory[ip] == EIF:
                        depth -= 1
        elif op == EIF:
            if memory[mp]:
                depth = 1
                while depth:
                    ip = (ip - 1) & 0xffff
                    if memory[ip] == IF:
                        depth -= 1
                    elif memory[ip] == EIF:
                        depth += 1
        elif op == FWD:
            ip = (ip + 1) & 0xffff
            mp += memory[ip] + 1
            mp &= 0xffff
        elif op == BAK:
            ip = (ip + 1) & 0xffff
            mp -= memory[ip] + 1
            mp &= 0xffff
        elif op == INC:
            ip = (ip + 1) & 0xffff
            memory[mp] += memory[ip] + 1
            memory[mp] &= 0xff
        elif op == DEC:
            ip = (ip + 1) & 0xffff
            memory[mp] -= memory[ip] + 1
            memory[mp] &= 0xff
        elif op == CON:
            if sock:
                stdin.close()
                stdout.close()
                sock.close()
            host = socket.inet_ntoa(bytes(memory[mp: mp+4]))
            port = int.from_bytes(memory[mp+4: mp+6], 'big')
            if host == '0.0.0.0' and port == 0:
                sock = None
                stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
            else:
                try:
                    sock = socket.create_connection((host, port))
                except ConnectionError:
                    sys.exit("h0s7 5uXz0r5! c4N'7 c0Nn3<7 l0l0l0l0l l4m3R !!!")
                stdin = sock.create_file('rb')
                stdout = sock.create_file('wb')
        ip += 1
        ip &= 0xffff


if __name__ == '__main__':
    file = sys.stdin
    d = len(sys.argv) > 1 and sys.argv[1] == '-d' and sys.argv.pop(1)
    if len(sys.argv) > 1 and sys.argv[1] != '-':
        file = open(sys.argv[1])
    if d:
        dis(file.read())
    else:
        run(file.read())
