# -*- coding: utf-8 -*-
import math, cmath, re, struct, functools, operator, string, itertools

def isprime_re(n):
    return not re.match(r'^1?$|^(11+?)\1+$', '1'*n)


def tobase(n, b):
    digs = []
    while n:
        n, r = divmod(n, b)
        digs.append('0123456789abcdefghijklmnopqrstuvwxyz'[r])
    return ''.join(digs)[::-1] or '0'

def frombase(s, b):
    digs = dict(zip('0123456789abcdefghijklmnopqrstuvwxyz', range(math.ceil(b))))
    # return sum(digs[c]*b**i for i, c in enumerate(reversed(s.lower())))
    return functools.reduce(lambda n, c: n*b + digs[c], s.lower(), 0)


##def float_tobase(num, b, p=10, pad0=False):
##    p = max(p, 0)
##    ss = ['-'] if num < 0 else []
##    num = abs(num)
##    for i in range(int(math.log(max(num, 1), b)), -p-1, -1):
##        if i < 0 and not (num or pad0):
##            break
##        dig = int(num * b**-i)
##        if dig >= b:
##            dig -= 1
##        num -= dig * b**i
##        ss.append('0123456789abcdefghijklmnopqrstuvwxyz'[dig])
##        if i == 0:
##            ss.append('.')
##    return ''.join(ss)

def float_tobase(num, b, p=10, pad0=False):
    p = max(p, 0)
    ss = ['-'] if num < 0 else []
    num = abs(num)
    e = int(math.log(max(num, 1), b))
    num *= b**-e
    for i in range(e + p + 1):
        if i > e and not (num or pad0):
            break
        num, dig = math.modf(num)
        num *= b
        ss.append('0123456789abcdefghijklmnopqrstuvwxyz'[int(dig)])
        if i == e:
            ss.append('.')
    return ''.join(ss)

def float_frombase(s, b):
    exp = 0
    point = s.find('.')
    if point >= 0:
        exp = point + 1 - len(s)
        s = s[:point] + s[point + 1:]
    return float(frombase(s, b) * b**exp)


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


def byteswap(n, nb=2):
    return sum((n >> 8*i & 255) << 8*(nb-i-1) for i in range(nb))

def byteswap16(n):
    return (n & 255) << 8 | n >> 8

def byteswap32(n):
    return (n & 255) << 24 | (n & 65280) << 8 | n >> 8 & 65280 | n >> 24


def float_bits(num):
    import struct
    return int.from_bytes(struct.pack('<f', num), 'little')

def double_bits(num):
    import struct
    return int.from_bytes(struct.pack('<d', num), 'little')

def float_bitstr(num, sep=' '):
    s = '{:032b}'.format(float_bits(num))
    return s[:1] + sep + s[1:9] + sep + s[9:]

def double_bitstr(num, sep=' '):
    s = '{:064b}'.format(double_bits(num))
    return s[:1] + sep + s[1:12] + sep + s[12:]

def float_frombits(s):
    import struct
    if isinstance(s, str): s = int(s.replace(' ', ''), 2)
    return struct.unpack('<f', s.to_bytes(4, 'little'))[0]

def double_frombits(s):
    import struct
    if isinstance(s, str): s = int(s.replace(' ', ''), 2)
    return struct.unpack('<d', s.to_bytes(8, 'little'))[0]


def parse_roman(s):
    s = s.upper()
    digs = dict(I=1, V=5, X=10, L=50, C=100, D=500, M=1000)
    x = 0
    for i, c in enumerate(s):
        n = digs[c]
        if i+1 < len(s) and n < digs[s[i+1]]:
            n = -n
        x += n
    return x
from_roman = parse_roman

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


# def caesar_cipher(s, k):
#     A, a = ord('A'), ord('a')
#     return ''.join([chr((ord(c) - A + k) % 26 + A) if 'A' <= c <= 'Z' else
#                     chr((ord(c) - a + k) % 26 + a) if 'a' <= c <= 'z' else
#                     c for c in s])

def caesar_cipher(s, k):
    k %= 26
    lower, upper = string.ascii_lowercase, string.ascii_uppercase
    trans = str.maketrans(lower + upper, 
                          lower[k:] + lower[:k] + upper[k:] + upper[:k])
    return s.translate(trans)


def rot13(s):
    return caesar_cipher(s, 13)


def vigenere_encode(s, k):
    A, a = ord('A'), ord('a')
    if isinstance(k, str):
        k = [ord(c) - a for c in k.lower()]
    return ''.join([chr((ord(c) + ki - A) % 26 + A) if 'A' <= c <= 'Z'
               else chr((ord(c) + ki - a) % 26 + a) if 'a' <= c <= 'z'
               else c for c, ki in zip(s, itertools.cycle(k))])


def vigenere_decode(s, k):
    if isinstance(k, str):
        a = ord('a')
        k = [ord(c) - a for c in k.lower()]
    return vigenere_encode(s, [-ki for ki in k])


def divmod_ceil(x, y):
    q, r = divmod(x, -y)
    return -q, r


def divmod_round(x, y):
    q, r = divmod(x, y)
    r2 = 2*r
    if r2 > y or r2 == y and q & 1:
        q += 1
        r -= y
    return q, r


def divmod_trunc(x, y):
    xneg = x < 0
    yneg = y < 0
    if xneg:
        x = -x
    if yneg:
        y = -y
    q, r = divmod(x, y)
    if xneg:
        r = -r
    if xneg ^ yneg:
        q = -q
    return q, r


def bin2gray(n):
    return n ^ (n >> 1)


def gray2bin(n):
    mask = n >> 1
    while mask:
        n ^= mask
        mask >>= 1
    return n


def frac2dec(f, prec=None):
    from decimal import Decimal, Context, localcontext
    with localcontext(Context(prec=prec)):
        return Decimal(f.numerator) / Decimal(f.denominator)


def human_readable(n, prec=1, strip=True):
    n = int(n)
    power = min(max((n.bit_length() - 1) // 10, 0), 6)
    num = '{:.{}f}'.format(n / 1024**power, prec)
    if strip and '.' in num:
        num = num.rstrip('0').rstrip('.')
    return num + 'BKMGTPE'[power]


def download_size(url, readable=False):
    import requests
    resp = requests.head(url, allow_redirects=True)
    resp.raise_for_status()
    size = int(resp.headers['Content-Length'])
    if readable:
        return human_readable(size)
    return size


def running_avg(arr, axis=-1):
    import numpy as np
    arr = np.asarray(arr)
    return arr.cumsum(axis=axis) / (np.arange(arr.shape[axis]) + 1)


def least_upper_bound(t1, t2):
    for t in t2.mro():
        if issubclass(t1, t):
            return t


def rescale(x, a1, b1, a2, b2):
    return (x - a1) * (b2 - a2) / (b1 - a1) + a2


MORSE_TABLE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.',
    '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.'}

MORSE_TABLE_R = {v: k for k, v in MORSE_TABLE.items()}

def morse_encode(s):
    return ' '.join(MORSE_TABLE.get(c.upper(), '') for c in s)

def morse_decode(s):
    return ' '.join(''.join(MORSE_TABLE_R.get(c, c)
                            for c in w.split()) for w in s.split('  '))


ASCII_SUBS_R = {
    '"': ['“', '”', '″'],
    "'": ['‘', '’', '′'],
    '-': ['‒', '–', '—', '―', '−'],
    '|': ['¦'],
    '<': ['⟨'],
    '>': ['⟩'],
}

ASCII_SUBS = {vi: k for k, v in ASCII_SUBS_R.items() for vi in v}

ASCII_SUBS_MULTI = {
    '…': '...',
    '←': '<-',
    '→': '->',
    '↔': '<->',
    '⇐': '<=',
    '⇒': '=>',
    '⇔': '<=>',
}

def asciify(s, multi_subs=True):
    s = unicodedata.normalize('NFKD', s)
    s2 = []
    for c in s:
        c = ASCII_SUBS.get(c, c)
        if multi_subs:
            c = ASCII_SUBS_MULTI.get(c, c)
        if c.isspace():
            c = ' '
        if c <= '~' and c.isprintable():
            s2.append(c)
    return ''.join(s2)


def comb(n, m):
    if m > n: return 0
    m = min(m, n-m)
    A = [1] * (m+1)
    for i in range(1, n-m+1):
        for j in range(1, m+1):
            A[j] += A[j-1]
    return A[m]

def prod(x):
    return functools.reduce(operator.mul, x, 1)

def comb(n, m):
    if m > n: return 0
    m = min(m, n-m)
    return prod(n-i for i in range(m)) // prod(i for i in range(1, m+1))


def nthroots(z, n):
    r = abs(z)**(1/n)
    a = cmath.phase(z)
    return [r * cmath.exp((a+2*math.pi*k)*1j/n) for k in range(n)]


def randcolor(h=(0, 1), s=(.75, 1), v=(.75, 1), a=None):
    import colorsys
    h = random.uniform(*h) if isinstance(h, tuple) else h
    s = random.uniform(*s) if isinstance(s, tuple) else s
    v = random.uniform(*v) if isinstance(v, tuple) else v
    c = colorsys.hsv_to_rgb(h, s, v)
    if a is not None:
        a = random.uniform(*a) if isinstance(a, tuple) else a
        c += (a,)
    return c

def randcolor_pg(h=(0, 360), s=(75, 100), v=(75, 100), a=100):
    from pygame import Color
    c = Color(0, 0, 0)
    h = random.uniform(*h) if isinstance(h, tuple) else h
    s = random.uniform(*s) if isinstance(s, tuple) else s
    v = random.uniform(*v) if isinstance(v, tuple) else v
    a = random.uniform(*a) if isinstance(a, tuple) else a
    c.hsva = (h, s, v, a)
    return c


def lerp(x0, x1, t):
    return x0*(1-t) + x1*t

def unlerp(x0, x1, x):
    return (x - x0) / (x1 - x0)

def log_interp(x0, x1, t):
##    return x0**(1-t) * x1**t
    return x0 * (x1 / x0)**t

def lerp_angle(a0, a1, t, amax=2*math.pi):
    min_angle = ((a1 - a0) - amax/2) % -amax + amax/2
    return (a0 + min_angle*t) % amax


def lerp_color(c0, c1, t):
    import colorsys
    a = None
    if len(c0) == 4 and len(c1) == 4:
        c0, a0 = c0[:3], c0[3]
        c1, a1 = c1[:3], c1[3]
        a = a0 + (a1 - a0)*t
    h0, s0, v0 = colorsys.rgb_to_hsv(*c0)
    h1, s1, v1 = colorsys.rgb_to_hsv(*c1)
    h = lerp_angle(h0, h1, t, 1)
    s = s0 + (s1 - s0)*t
    v = v0 + (v1 - v0)*t
    c = colorsys.hsv_to_rgb(h, s, v)
    if a is not None:
        c += (a,)
    return c

def lerp_color_pg(c0, c1, t):
    from pygame import Color
    h0, s0, v0, a0 = Color(*c0).hsva
    h1, s1, v1, a1 = Color(*c1).hsva
    h = lerp_angle(h0, h1, t, 360)
    s = s0 + (s1 - s0)*t
    v = v0 + (v1 - v0)*t
    a = a0 + (a1 - a0)*t
    c = Color(0, 0, 0)
    c.hsva = (h, s, v, a)
    return c


def geom_cdf(p, k):
    return -math.expm1(k*math.log1p(-p))


def gauss_kernel_1d(k, sigma=None):
    import numpy as np
    if sigma is None:
        sigma = (k-1)/6
    x = np.arange(k) - (k-1)/2
    z = np.exp(-x**2/(2*sigma**2))
    return z / z.sum()

def gauss_kernel_2d(k, sigma=None):
    import numpy as np
    k1 = gauss_kernel_1d(k, sigma)
    return np.outer(k1, k1)
