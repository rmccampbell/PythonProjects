import struct

def fp2float(i):
    return struct.unpack('>f', i.to_bytes(4, 'big'))[0]

def float2fp(f):
    return int.from_bytes(struct.pack('>f', f), 'big')

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
    sgn = i>>31 & 1
    exp = (i>>23 & 0xff) - 127 - 23
    mant = i & 0x7fffff | 1<<23
    if exp == -127 - 23:  # zero and subnormal
        mant &= 0x7fffff
        exp += 1
    return sgn, exp, mant

def fp_normalize(sgn, exp, mant):
    n = mant.bit_length() - 24
    exp += n
    if mant == 0:  # zero
        exp = -127 - 23
    if exp <= -127 - 23:  # subnormal
        n += -127 - 23 - exp + 1
        exp = -127 - 23
    elif exp >= 255 - 127 - 23:  # infinity
        mant = 0
        exp = 255 - 127 - 23
    if n >= 0:
        mant >>= n
    else:
        mant <<= -n
    return sgn << 31 | exp + 127 + 23 << 23 | mant & 0x7fffff

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
        exp = 255 - 127 - 23
        if mant1 == 0:
            mant = 0xc00000
        else:
            mant = 0x800000
    else:
        mant = (mant1<<23) // mant2
        exp = exp1 - exp2 - 23
    sgn = sgn1 ^ sgn2
    return fp_normalize(sgn, exp, mant)
