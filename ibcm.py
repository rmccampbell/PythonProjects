#!/usr/bin/env python3
import sys, argparse, ast

HALT  = 0x0
IO    = 0x1
SHIFT = 0x2
LOAD  = 0x3
STORE = 0x4
ADD   = 0x5
SUB   = 0x6
AND   = 0x7
OR    = 0x8
XOR   = 0x9
NOT   = 0xa
NOP   = 0xb
JMP   = 0xc
JMPE  = 0xd
JMPL  = 0xe
BRL   = 0xf

READH = SHIFTL = 0x0
READ = SHIFTR = 0x1
WRITEH = ROTL = 0x2
WRITE = ROTR = 0x3

OPCODES = {
    'halt':     0x0,
    'readh':    0x1,
    'read':     0x1,
    'printh':   0x1,
    'print':    0x1,
    'shiftl':   0x2,
    'shiftr':   0x2,
    'rotl':     0x2,
    'rotr':     0x2,
    'load':     0x3,
    'store':    0x4,
    'add':      0x5,
    'sub':      0x6,
    'and':      0x7,
    'or':       0x8,
    'xor':      0x9,
    'not':      0xa,
    'nop':      0xb,
    'jmp':      0xc,
    'jmpe':     0xd,
    'jmpl':     0xe,
    'brl':      0xf,
}

IO_OPS = {
    'readh':    0x0,
    'read':     0x1,
    'printh':   0x2,
    'print':    0x3,
}

SHIFT_OPS = {
    'shiftl':   0x0,
    'shiftr':   0x1,
    'rotl':     0x2,
    'rotr':     0x3,
}


def parse_array(s):
    try:
        objs = ast.literal_eval(s)
    except ValueError:
        raise ValueError('invalid data declaration')
    if not isinstance(objs, tuple):
        objs = (objs,)
    arr = []
    for obj in objs:
        if isinstance(obj, int):
            arr.append(obj & 0xffff)
        elif isinstance(obj, str):
            arr.extend(ord(c) & 0xffff for c in obj)
        else:
            raise ValueError('invalid data declaration')
    return arr

def assemble(code):
    code = code.splitlines()
    toklst = []
    mcode = []
    labels = {}
    for i, l in enumerate(code):
        toks = [t.strip() for t in l.split('\t', 3)]
        toks.extend([''] * (4 - len(toks)))
        toklst.append(toks)
        label = toks[0]
        if label:
            labels[label] = i
    for i, toks in enumerate(toklst):
        label, opname, data, comment = toks
        opval = 0
        if opname == 'dw':
            if data.startswith("'"):
                opval = ord(ast.literal_eval(data))
            elif data:
                opval = int(data, 16)
        elif opname:
            opcode = OPCODES[opname.lower()]
            if opcode == IO:
                io_op = IO_OPS[opname.lower()]
                oparg = io_op << 10
            elif opcode == SHIFT:
                shift_op = SHIFT_OPS[opname.lower()]
                oparg = shift_op << 10 | (int(data, 16) & 0xf)
            else:
                oparg = 0
                if '+' in data:
                    lbl, off = data.split('+', 1)
                    oparg = labels[lbl.strip()] + int(off, 16)
                elif data:
                    try:
                        oparg = int(data, 16)
                    except ValueError:
                        oparg = labels[data]
            opval = opcode << 12 | oparg
        line = '%04X %03X %s\t%s\t%s\t%s' % (
            opval, i, label, opname, data, comment)
        line = line.rstrip().replace(' \t', '\t')
        mcode.append(line)
    return '\n'.join(mcode) + '\n'


def interpret(code):
    mem = [0] * 0x1000
    for i, l in enumerate(code.splitlines()):
        mem[i] = int(l[:4], 16)
    pc = 0
    accum = 0
    while pc < len(mem):
        instr = mem[pc]
        op = instr >> 12
        addr = instr & 0xfff
        if op == HALT:
            break
        elif op == IO:
            ioop = addr >> 10
            if ioop == READH:
                accum = int(input(), 16)
            elif ioop == READ:
                char = sys.stdin.read(1)
                accum = ord(char) if char else 0 # 0 for EOF
            elif ioop == WRITEH:
                print('{:04x}'.format(accum))
            elif ioop == WRITE:
                sys.stdout.write(chr(accum))
        elif op == SHIFT:
            shiftop = addr >> 10
            cnt = addr & 0xf
            if shiftop == SHIFTL:
                accum <<= cnt
            elif shiftop == SHIFTR:
                accum >>= cnt
            elif shiftop == ROTL:
                accum = accum << cnt | accum >> (16 - cnt)
            elif shiftop == ROTR:
                accum = accum >> cnt | accum << (16 - cnt)
        elif op == LOAD:
            accum = mem[addr]
        elif op == STORE:
            mem[addr] = accum
        elif op == ADD:
            accum += mem[addr]
        elif op == SUB:
            accum -= mem[addr]
        elif op == AND:
            accum &= mem[addr]
        elif op == OR:
            accum |= mem[addr]
        elif op == XOR:
            accum ^= mem[addr]
        elif op == NOT:
            accum = ~accum
        elif op == NOP:
            pass
        elif op == JMP:
            pc = addr - 1
        elif op == JMPE:
            if accum == 0:
                pc = addr - 1
        elif op == JMPL:
            if accum & 0x8000: # accum < 0
                pc = addr - 1
        elif op == BRL:
            accum = pc + 1
            pc = addr - 1
        accum &= 0xffff
        pc += 1


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('ifile', nargs='?', type=argparse.FileType('r'), default='-')
    p.add_argument('ofile', nargs='?', type=argparse.FileType('w'), default='-')
    p.add_argument('-a', '--assemble', action='store_true')
    args = p.parse_args()
    if args.assemble:
        mcode = assemble(args.ifile.read())
        args.ofile.write(mcode)
    else:
        interpret(args.ifile.read())
