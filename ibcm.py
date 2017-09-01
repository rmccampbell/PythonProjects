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
READC = SHIFTR = 0x1
PRINTH = ROTL = 0x2
PRINTC = ROTR = 0x3

OPCODES = {
    'halt':     HALT,
    'readh':    IO,
    'readc':    IO,
    'printh':   IO,
    'printc':   IO,
    'shiftl':   SHIFT,
    'shiftr':   SHIFT,
    'rotl':     SHIFT,
    'rotr':     SHIFT,
    'load':     LOAD,
    'store':    STORE,
    'add':      ADD,
    'sub':      SUB,
    'and':      AND,
    'or':       OR,
    'xor':      XOR,
    'not':      NOT,
    'nop':      NOP,
    'jmp':      JMP,
    'jmpe':     JMPE,
    'jmpl':     JMPL,
    'brl':      BRL,
}

IO_OPS = {
    'readh':    0x0,
    'readc':     0x1,
    'printh':   0x2,
    'printc':    0x3,
}

SHIFT_OPS = {
    'shiftl':   0x0,
    'shiftr':   0x1,
    'rotl':     0x2,
    'rotr':     0x3,
}


def parse_array(s):
    msg = 'invalid data declaration'
    if '(' in s:
        raise ValueError(msg)
    try:
        objs = ast.literal_eval(s)
    except (SyntaxError, ValueError):
        raise ValueError(msg)
    if not isinstance(objs, tuple):
        objs = (objs,)
    arr = []
    for obj in objs:
        if isinstance(obj, int):
            arr.append(obj & 0xffff)
        elif isinstance(obj, str):
            arr.extend(ord(c) & 0xffff for c in obj)
        else:
            raise ValueError(msg)
    if not arr:
        raise ValueError(msg)
    return arr

def assemble(code):
    code = code.splitlines()
    toklst = []
    mcode = []
    labels = {}
    i = 0
    for l in code:
        if not l.strip():
            continue
        toks = [t.strip() for t in l.split('\t', 3)]
        toks.extend([''] * (4 - len(toks)))
        label, opname, data, comment = toks
        if label:
            labels[label] = i
        if opname == 'dw':
            datas = parse_array(data)
            toklst.append([datas[0]] + toks)
            toklst.extend([[data, '', '', '', ''] for data in datas[1:]])
            i += len(datas)
        else:
            toklst.append([0] + toks)
            i += 1
    for i, (opval, label, opname, data, comment) in enumerate(toklst):
        if opname and opname != 'dw':
            opcode = OPCODES[opname.lower()]
            if opcode == IO:
                io_op = IO_OPS[opname.lower()]
                oparg = io_op << 10
            elif opcode == SHIFT:
                shift_op = SHIFT_OPS[opname.lower()]
                oparg = shift_op << 10 | (int(data, 0) & 0xf)
            else:
                oparg = 0
                if '+' in data:
                    lbl, off = data.split('+', 1)
                    oparg = labels[lbl.strip()] + int(off, 0)
                elif data:
                    try:
                        oparg = int(data, 0)
                    except ValueError:
                        oparg = labels[data]
            opval = opcode << 12 | oparg
        line = '%04X %03X %s\t%s\t%s\t%s' % (
            opval, i, label, opname, data, comment)
        line = line.rstrip().replace(' \t', '\t')
        mcode.append(line)
    return '\n'.join(mcode) + '\n'


def execute(code):
    mem = [0] * 0x1000
    for i, l in enumerate(code.splitlines()):
        mem[i] = int(l[:4], 16)
    pc = 0
    accum = 0
    while pc < len(mem):
        instr = mem[pc]
        op = instr >> 12
        addr = args = instr & 0xfff
        if op == HALT:
            break
        elif op == IO:
            ioop = args >> 10
            if ioop == READH:
                accum = int(input(), 16)
            elif ioop == READC:
                char = sys.stdin.read(1)
                accum = ord(char) if char else 0 # 0 for EOF
            elif ioop == PRINTH:
                print('{:04x}'.format(accum))
            elif ioop == PRINTC:
                sys.stdout.write(chr(accum))
        elif op == SHIFT:
            shiftop = args >> 10
            cnt = args & 0xf
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
        execute(args.ifile.read())
