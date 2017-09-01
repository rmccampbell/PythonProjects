import struct

DIG = EOFF = 23
MMASK = (1 << DIG) - 1
TDIG = DIG + 1
EXP = 8
EMASK = (1 << EXP) - 1
BIAS = (1 << EXP-1) - 1
IBIAS = BIAS + DIG
SOFF = DIG + EXP
MINEXP = -IBIAS
MAXEXP = EMASK - IBIAS
INF = EMASK << EOFF
NAN = EMASK << EOFF | 1 << DIG-1

def fp2float(i):
    return struct.unpack('<f', i.to_bytes(4, 'little'))[0]

def float2fp(f):
    return int.from_bytes(struct.pack('<f', f), 'little')

def fp2int(i):
    sgn, exp, mant = fp_split(i)
    if exp >= 0:
        mag = mant << exp
    else:
        mag = mant >> -exp
    return -mag if sgn else mag

def int2fp(i):
    sgn, mant = int(i < 0), abs(i)
    return fp_normalize(sgn, 0, mant)

def fp_split(i):
    if isinstance(i, tuple):
        return i
    elif isinstance(i, float):
        i = float2fp(i)
    sgn = i>>SOFF & 1
    exp = (i>>EOFF & EMASK) - IBIAS
    mant = i & MMASK | 1<<DIG
    if exp == MINEXP:  # zero and subnormal
        mant &= MMASK
        exp += 1
    return sgn, exp, mant

def fp_normalize(sgn, exp, mant):
    n = mant.bit_length() - TDIG
    exp += n
    if mant == 0:  # zero
        exp = MINEXP
    if exp <= MINEXP:  # subnormal
        n += MINEXP - exp + 1
        exp = MINEXP
    elif exp >= MAXEXP:  # infinity
        mant = 0
        exp = MAXEXP
    if n >= 0:
        mant >>= n
    else:
        mant <<= -n
    return sgn << SOFF | exp+IBIAS << EOFF | mant & MMASK

def fp_neg(a):
    if isinstance(a, tuple):
        a = fp_normalize(*a)
    elif isinstance(a, float):
        a = float2fp(a)
    return a ^ (1 << SOFF)

def fp_add(a, b):
    sgn1, exp1, mant1 = fp_split(a)
    sgn2, exp2, mant2 = fp_split(b)
    exp = min(exp1, exp2)
    mant1 <<= exp1 - exp
    mant2 <<= exp2 - exp
    mant1 = -mant1 if sgn1 else mant1
    mant2 = -mant2 if sgn2 else mant2
    mant = mant1 + mant2
    sgn, mant = int(mant < 0), abs(mant)
    return fp_normalize(sgn, exp, mant)

def fp_sub(a, b):
    sgn1, exp1, mant1 = fp_split(a)
    sgn2, exp2, mant2 = fp_split(b)
    exp = min(exp1, exp2)
    mant1 <<= exp1 - exp
    mant2 <<= exp2 - exp
    mant1 = -mant1 if sgn1 else mant1
    mant2 = -mant2 if sgn2 else mant2
    mant = mant1 - mant2
    sgn, mant = int(mant < 0), abs(mant)
    return fp_normalize(sgn, exp, mant)

def fp_mul(a, b):
    sgn1, exp1, mant1 = fp_split(a)
    sgn2, exp2, mant2 = fp_split(b)
    mant = mant1 * mant2
    exp = exp1 + exp2
    sgn = sgn1 ^ sgn2
    return fp_normalize(sgn, exp, mant)

def fp_div(a, b):
    sgn1, exp1, mant1 = fp_split(a)
    sgn2, exp2, mant2 = fp_split(b)
    if mant2 == 0:
        if mant1 == 0:  # nan
            return NAN
        else:  # infinity
            return INF
    else:
        mant = (mant1 << DIG) // mant2
        exp = exp1 - exp2 - DIG
    sgn = sgn1 ^ sgn2
    return fp_normalize(sgn, exp, mant)

def fp_sqrt(a):
    sgn, exp, mant = fp_split(a)
    if sgn and mant:
        return NAN
    if exp & 1:
        exp -= 1
        mant <<= 1
    mant <<= TDIG
    exp -= TDIG
    y = 0
    for i in range(TDIG, -1, -1):
        y2 = y | 1<<i
        if y2*y2 <= mant:
            y = y2
    return fp_normalize(0, exp >> 1, y)

def fp_str(a):
    sgn, exp, mant = fp_split(a)
    e10 = (exp * 0x13441 >> 18) + 1 # approx exp * log10(2)
    if exp >= 0:
        x = (mant << exp) // 10**e10
    else:
        x = mant * 10**-e10 >> -exp
    s = str(x)
    if e10 >= 0:
        return s + '0'*e10 + '.'
    elif e10 <= -len(s):
        return '.' + s.rjust(-e10, '0')
    return s[:e10] + '.' + s[e10:]

def fp_sin(a):
    pass
