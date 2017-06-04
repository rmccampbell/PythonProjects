import math, re, struct, functools

def isprime_re(n):
    return not re.match(r'^1?$|^(11+?)\1+$', '1'*n)


def tobase(n, b):
    digs = []
    while n:
        n, r = divmod(n, b)
        digs.append('0123456789abcdefghijklmnopqrstuvwxyz'[r])
    return ''.join(digs)[::-1] or '0'

def frombase(s, b):
    digs = dict(zip('0123456789abcdefghijklmnopqrstuvwxyz', range(b)))
    #return sum(digs[c]*b**i for i, c in enumerate(reversed(s)))
    return functools.reduce(lambda n, c: n*b + digs[c], s, 0)


def nthbit(x, n):
    return x >> n & 1

def revbits(x, n=8):
    y = 0
    for i in range(n):
        y = y << 1 | x & 1
        x >>= 1
    return y

def revbits2(x, n=8):
    table = (0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15)
    y = 0
    m, r = divmod(n, 4)
    for i in range(m):
        y = y << 4 | table[x & 0xf]
        x >>= 4
    if r:
        y = y << r | table[x & 0xf] >> 4-r
    return y

def revbits32(x):
    x = (x & 0x55555555) << 1 | x >> 1 & 0x55555555
    x = (x & 0x33333333) << 2 | x >> 2 & 0x33333333
    x = (x & 0x0f0f0f0f) << 4 | x >> 4 & 0x0f0f0f0f
    x = (x & 0x00ff00ff) << 8 | x >> 8 & 0x00ff00ff
    return (x & 0x0000ffff) << 16 | x >> 16

def rotbits(x, y, n=8):
    mask = (1<<n) - 1
    return x << y%n & mask | (x & mask) >> -y%n

def bitcount(n):
    i = 0
    while n:
        n &= n-1
        i += 1
    return i

def bitcount32(n):
    n = (n & 0x55555555) + (n >> 1 & 0x55555555)
    n = (n & 0x33333333) + (n >> 2 & 0x33333333)
    n = (n & 0x0f0f0f0f) + (n >> 4 & 0x0f0f0f0f)
    n = (n & 0x00ff00ff) + (n >> 8 & 0x00ff00ff)
    return (n & 0x0000ffff) + (n >> 16)

def parity(n):
    i = 0
    while n:
        n &= n-1
        i ^= 1
    return i

def parity32(n):
    n ^= n >> 16
    n ^= n >> 8
    n ^= n >> 4
    n ^= n >> 2
    n ^= n >> 1
    return n & 1


def float_bits(num):
    import struct
    return int.from_bytes(struct.pack('>f', num), 'big')

def double_bits(num):
    import struct
    return int.from_bytes(struct.pack('>d', num), 'big')

def float_bitstr(num, sep=' '):
    s = '{:032b}'.format(float_bits(num))
    return s[:1] + sep + s[1:9] + sep + s[9:]

def double_bitstr(num, sep=' '):
    s = '{:064b}'.format(double_bits(num))
    return s[:1] + sep + s[1:12] + sep + s[12:]

def float_frombits(s):
    import struct
    if isinstance(s, str): s = int(s.replace(' ', ''), 2)
    return struct.unpack('>f', s.to_bytes(4, 'big'))[0]

def double_frombits(s):
    import struct
    if isinstance(s, str): s = int(s.replace(' ', ''), 2)
    return struct.unpack('>d', s.to_bytes(8, 'big'))[0]


def from_roman(s):
    digs = dict(I=1, V=5, X=10, L=50, C=100, D=500, M=1000)
    x = 0
    for i, c in enumerate(s):
        n = digs[c]
        if i+1 < len(s) and n < digs[s[i+1]]:
            n = -n
        x += n
    return x

def roman(n):
    ones = ' I II III IV V VI VII VIII IX'.split(' ')
    tens = ' X XX XXX XL L LX LXX LXXX XC'.split(' ')
    hunds = ' C CC CCC CD D DC DCC DCCC CM'.split(' ')
    return 'M'*(n//1000) + hunds[n//100%10] + tens[n//10%10] + ones[n%10]


def concat_lists(lists):
    ret = []
    for l in lists:
        ret += l
    return ret


def as_integer_ratio(f):
    m, e = math.frexp(f)
    m = int(math.ldexp(m, 53))
    e -= 53
    if e >= 0:
        return m << e, 1
    n = (m ^ (m-1)).bit_length() - 1 # trailing zeros
    if -e <= n:
        return m >> -e, 1
    return m >> n, 1 << -e-n


def caesar_cipher(s, k):
    return ''.join([chr((ord(c) - 65 + k) % 26 + 65) if 'A' <= c <= 'Z' else \
                    chr((ord(c) - 97 + k) % 26 + 97) if 'a' <= c <= 'z' else \
                    c for c in s])


def divmod_ceil(x, y):
    q = (x - 1) // y + 1
    return q, x - y*q


def divmod_round(x, y):
    q, r = divmod(x, y)
    r2 = 2*r
    if r2 > x or r2 == x and q % 2:
        q += 1
        r -= y
    return q, r
