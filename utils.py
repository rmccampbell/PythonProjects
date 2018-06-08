from __future__ import print_function, division
del print_function, division

import sys
_PY3 = sys.version_info[0] >= 3

# Builtin imports
import os, collections, functools, itertools, operator, types, math, cmath, re
import io, random, inspect, textwrap, dis, timeit, time, datetime, string
import fractions, decimal, unicodedata, codecs, locale, shutil, numbers
from math import pi, e, sqrt, exp, log, log10, floor, ceil, factorial, \
     sin, cos, tan, asin, acos, atan, atan2
inf = float('inf')
nan = float('nan')
deg = pi/180
from functools import partial, reduce
from itertools import islice, chain, starmap
from collections import OrderedDict, Counter
from fractions import Fraction
from decimal import Decimal
if _PY3:
    from itertools import zip_longest
    try: from math import log2
    except ImportError: pass
    try: from math import gcd
    except ImportError: from fractions import gcd
    try: from importlib import reload
    except ImportError: from imp import reload
    import urllib.request
    from urllib.request import urlopen

# My imports
import utils, functools2
from functools2 import autocurrying, chunk, comp, ncomp, ident, inv, supply, \
     rpartial, trycall, trywrap, tryiter, iterfunc, unique, is_sorted, ilen, \
     iindex, flatten, deepcopy, deepmap, first, last, unzip, take, pad, window
from functools2 import update_wrapper_signature as _update_wrapper
if _PY3:
    import classes
    from classes import DictNS, Symbol, ReprStr, BinInt, HexInt, PrettyODict
for m in 'misc primes num2words'.split():
    try:
        exec('import %s' % m)
    except ImportError:
        pass
del m

# 3rd Party imports
try:
    import more_itertools
except ImportError:
    pass

T, F, N = True, False, None

_empty = functools2.Sentinel('<empty>')


def flocals(depth=0):
    return sys._getframe(depth + 1).f_locals

def fglobals(depth=0):
    return sys._getframe(depth + 1).f_globals


def func(code, name=None, globs=None):
    if globs is None:
        globs = fglobals(1)
    if name is None:
        exclude = globs.copy()
    if isinstance(code, str):
        code = textwrap.dedent(code)

    exec(code, globs)
    if name is not None:
        return globs[name]
    else:
        for n, v in sorted(globs.items()):
            if not n.startswith('_') and (n, v) not in exclude.items():
                return v
        raise ValueError('nothing to return')

def impt(string, _depth=0):
    if not isinstance(string, str): return string
    globs = fglobals(_depth+1)

    dotnames = re.findall(r'(?<!\.)\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', string)
    for dotname in dotnames:
        names = dotname.split('.')
        for i, name in enumerate(names):
            try:
                eval(dotname, globs)
                break
            except NameError as e:
                try: globs[name] = __import__(name)
                except ImportError: break
            except AttributeError as e:
                try: __import__('.'.join(names[:i+1]))
                except ImportError: break
    return eval(string, globs)

class pipe(object):
    def __init__(self, callable_, *args, **kwargs): #wrapcall=False, **kwargs):
        self._wrapcall = kwargs.pop('wrapcall', False) #wrapcall

        if args or kwargs:
            self.callable = partial(callable_, *args, **kwargs)
        else:
            self.callable = callable_

        if isinstance(callable_, (type, pipe)):
            updated = ()
        else:
            updated = functools.WRAPPER_UPDATES
        try:
            _update_wrapper(self, callable_, updated=updated)
        except AttributeError:
            _update_wrapper(self, callable_, ('__doc__',), updated)

    def __repr__(self):
        return '<utils.pipe of {!r}>'.format(self.callable)

    def __or__(self, other):
        if isinstance(other, pipe):
            return other.__ror__(self)

    def __ror__(self, other):
        if isinstance(other, tuple):
            try:
                res = self.callable(*other)
            except TypeError:
                res = self.callable(other)
        else:
            res = self.callable(other)
        if self._wrapcall and callable(res) and not isinstance(res, pipe):
            return pipe(res)
        return res

    def __call__(self, *args, **kwargs):
        res = self.callable(*args, **kwargs)
        if self._wrapcall and callable(res) and not isinstance(res, pipe):
            return pipe(res)
        return res

    def __getattr__(self, name):
        return getattr(self.callable, name)
call = pipe


def cblock(code, globs=None, locs=None):
    #can see globals but won't modify them by default
    if globs is None:
        globs = fglobals(1)
    if locs is None:
        locs = {}
    if isinstance(code, str):
        code = textwrap.dedent(code)
    exec(code, globs, locs)
    return locs

def rename(obj, name=None, qualname=None):
    if name is None and qualname in (None, True, False):
        return obj
    if _PY3:
        if qualname is None:
            obj.__qualname__ = name
        elif qualname is True:
            pref = obj.__qualname__.rsplit('.', 1)[0]
            obj.__qualname__ = pref + '.' + name
        elif qualname is not False:
            obj.__qualname__ = qualname
    if name is not None:
        obj.__name__ = name
    return obj

def method(cls):
    def method(func):
        func.__qualname__ = cls.__name__ + '.' + func.__name__
        setattr(cls, func.__name__, func)
        return func
    return method

@pipe
def loop(it):
##    collections.deque(it, maxlen=0)
    for x in it:
        pass

def each(func, it=None):
    if it is None:
        return pipe(lambda it: each(func, it))
    for x in it:
        func(x)

def getl(name, depth=0):
    return flocals(depth + 1)[name]

def setl(_name=None, _value=None, _depth=0, **kws):
    flocals(_depth+1).update(kws)
    if _name is not None:
        flocals(_depth + 1)[_name] = _value
        return _value

def getg(name, depth=0):
    return fglobals(depth + 1)[name]

def setg(_name=None, _value=None, _depth=0, **kws):
    fglobals(_depth + 1).update(kws)
    if _name is not None:
        fglobals(_depth + 1)[_name] = _value
        return _value

def seta(_obj, _name=None, _value=None, **kws):
    if _name is not None:
        setattr(_obj, _name, _value)
    for name, value in kws.items():
        setattr(_obj, name, value)
    return _obj

@pipe
def void(*args):
    pass

def clip(n, low, high):
    return min(max(n, low), high)

def randints(size=10, max=10):
    return [random.randrange(max) for i in range(size)]

def randbytes(n):
    return random.getrandbits(8 * n).to_bytes(n, 'little')

def crange(start, stop, inclusive=True, nonchars=True):
    start = start if isinstance(start, int) else ord(start)
    stop = stop if isinstance(stop, int) else ord(stop)
    if inclusive: stop += 1
    return ''.join([c for c in map(chr, range(start, stop))
                    if nonchars or unicodedata.category(c) != 'Cn'])

def brange(start, stop, inclusive=True):
    start = start if isinstance(start, int) else ord(start)
    stop = stop if isinstance(stop, int) else ord(stop)
    if inclusive: stop += 1
    return bytes(range(start, stop))

def nextchr(c, off=1):
    chrf = bchr if isinstance(c, bytes) else chr
    return chrf(ord(c) + off)

def prevchr(c, off=1):
    chr = bchr if isinstance(c, bytes) else chr
    return chr(ord(c) - off)

def letters(num=26):
    return ''.join(islice(itertools.cycle(string.ascii_lowercase), num))

def randletters(num=10, mixedcase=False):
    letters = string.ascii_letters if mixedcase else string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(num))

def randwords(num=10, size=10, stdev=1, mixedcase=False):
    return [randletters(max(1, int(random.gauss(size, stdev))), mixedcase)
            for i in range(num)]

rletters = randletters
rwords = randwords

def shuffled(it):
    lst = list(it)
    random.shuffle(lst)
    return lst


def randcolor(h=(0, 360), s=(75, 100), v=(75, 100), a=100):
    from pygame import Color
    c = Color(0, 0, 0)
    h = random.randrange(*h) if isinstance(h, tuple) else h
    s = random.randint(*s) if isinstance(s, tuple) else s
    v = random.randint(*v) if isinstance(v, tuple) else v
    a = random.randint(*a) if isinstance(a, tuple) else a
    c.hsva = (h, s, v, a)
    return c


def interp_angle(a0, a1, t, max=2*math.pi):
    min_angle = ((a1 - a0) + max/2) % max - max/2
    return (a0 + min_angle*t) % max


def interp_color(c0, c1, t):
    from pygame import Color
    h0, s0, v0, a0 = c0.hsva
    h1, s1, v1, a1 = c1.hsva
    h = interp_angle(h0, h1, t, 360)
    s = s0 + (s1 - s0)*t
    v = v0 + (v1 - v0)*t
    a = a0 + (a1 - a0)*t
    c = Color(0, 0, 0)
    c.hsva = (h, s, v, a)
    return c


def schunk(s, size=2):
    for i in range(0, len(s), size):
        yield s[i : i+size]
##    return map(''.join, chunk(s, size, dofill=False))

def sgroup(s, size=2, sep=None):
    if sep is None:
        sep = ' ' if isinstance(s, str) else b' '
    return sep.join(schunk(s, size))

def spartition(s, *inds):
    prev = 0
    for ind in inds:
        yield s[prev:ind]
        prev = ind
    yield s[prev:]

def sbreak(s, inds, sep=None):
    if sep is None:
        sep = ' ' if isinstance(s, str) else b' '
    return sep.join(spartition(s, *inds))

def sinsert(s, ind, s2):
    return s[:ind] + s2 + s[ind:]

def sfilter(func, s):
    return ''.join(filter(func, s))

def smap(func, s):
    return ''.join(map(str, map(func, s)))


def strbin(s, enc='utf-8', sep=' '):
    if isinstance(s, str):
        s = s.encode(enc)
    return sep.join(map('{:08b}'.format, s))

def strhex(s, enc=None):
    import binascii
    if isinstance(s, str):
        if enc is None:
            maxc = max(s)
            enc = ('latin-1' if maxc <= '\xff' else
                   'utf-16be' if maxc <= '\uffff' else 'utf-32be')
        s = s.encode(enc)
    return binascii.hexlify(s).decode('ascii')

def bytesfrombin(s):
    return bytes(int(bits, 2) for bits in schunk(''.join(s.split()), 8))

def strfrombin(s, enc='utf-8'):
    return bytes_frombin(s).decode(enc)

def strfromhex(s, enc='utf-8'):
    return bytes.fromhex(s).decode(enc)

def unsigned(x, n=8):
    return x & (1<<n)-1

def signed(x, n=8):
    sb = 1<<(n-1)
    return (x & (1<<n)-1 ^ sb) - sb

_signed = signed
def tobytes(n, length=None, byteorder=sys.byteorder, signed=False):
    if isinstance(length, str):
        length, byteorder = None, length
    byteorder = {'<': 'little', '>': 'big', '=': sys.byteorder}.get(
        byteorder, byteorder)
    if length is None:
        bl = (n if n >= 0 else ~n).bit_length() + 1 if signed \
             else n.bit_length()
        length = (bl + 7) // 8
    elif signed:
        n = _signed(n, 8*length)
    else:
        n = unsigned(n, 8*length)
    return n.to_bytes(length, byteorder, signed=signed)

def frombytes(bts, byteorder=sys.byteorder, signed=False):
    byteorder = {'<': 'little', '>': 'big', '=': sys.byteorder}.get(
        byteorder, byteorder)
    return int.from_bytes(bts, byteorder, signed=signed)

def blen(n, signed=False):
    if signed:
        return (n if n >= 0 else ~n).bit_length() + 1
    return n.bit_length()

def binfmt(n, bits=8, sign=False, prefix=False):
    if hasattr(n, 'dtype'):
        bits = n.dtype.itemsize * 8
    pref = '#' if prefix else ''
    prefw = 2 if prefix else 0
    if sign:
        return '{: {}0{}b}'.format(signed(n, bits), pref, prefw+bits+1)
    return '{:{}0{}b}'.format(unsigned(n, bits), pref, prefw+bits)
binf = binfmt

def hexfmt(n, digs=8, sign=False, prefix=False):
    if hasattr(n, 'dtype'):
        digs = n.dtype.itemsize * 2
    pref = '#' if prefix else ''
    prefw = 2 if prefix else 0
    if sign:
        return '{: {}0{}x}'.format(signed(n, digs*4), pref, prefw+digs+1)
    return '{:{}0{}x}'.format(unsigned(n, digs*4), pref, prefw+digs)
hexf = hexfmt

def binint(x):
    return int(x, 2)

def hexint(x):
    return int(x, 16)

def float_binf(num, p=23, pad0=False, prefix=False):
    if p < 0 or p is None: p = 1074
    num, whole = math.modf(num)
    num = abs(num)
    ss = [format(int(whole), '#b' if prefix else 'b'), '.']
    for i in range(p):
        if not (num or pad0):
            break
        num, whole = math.modf(num * 2)
        ss.append('01'[int(whole)])
    return ''.join(ss)

def float_hexf(num, p=13, pad0=False, prefix=False):
    if p < 0 or p is None: p = 269
    num, whole = math.modf(num)
    num = abs(num)
    ss = [format(int(whole), '#x' if pref else 'x'), '.']
    for i in range(p):
        if not (num or pad0):
            break
        num, whole = math.modf(num * 16)
        ss.append('0123456789abcdef'[int(whole)])
    return ''.join(ss)

def float_bin(num, p=23):
    if p < 0: p = 52
    s = float(num).hex()
    if '0x' in s:
        i = s.index('.')+1
        j = s.index('p')
        m = int(s[i:j], 16)
        s = s[:i].replace('x', 'b') + binfmt(m, 52)[:p] + s[j:]
    return s

def float_frombin(s):
    s = s.strip()
    if re.search(r'\s', s):
        raise ValueError('invalid format')
    s, p, e = s.lower().partition('p')
    exp = int(e) if p else 0
    if '.' in s:
        exp -= len(s) - s.index('.') - 1
    return float(int(s.replace('.', '', 1), 2) * 2**exp)


@pipe
def head(s=None, n=10, wrap=True):
    if s is None:
        return pipe(head, n=n, wrap=wrap)
    if isinstance(s, int):
        return pipe(head, n=s, wrap=wrap)
    if wrap:
        s = textwrap.fill(str(s), 80, replace_whitespace=False)
    print(''.join(s.splitlines(True)[:n]))

@pipe
def tail(s, n=10, wrap=True):
    if s is None:
        return pipe(tail, n=n, wrap=wrap)
    if isinstance(s, int):
        return pipe(tail, n=s, wrap=wrap)
    if wrap:
        s = textwrap.fill(str(s), 80, replace_whitespace=False)
    print(''.join(s.splitlines(True)[-n:]))

@pipe
def more(s, h=24):
    s = str(s).splitlines(True)
    while s:
        hd, s = s[:h], s[h:]
        print(''.join(hd), end='')
        if s and input().lower() == 'q':
            break

def printr(o):
    print(o)
    return o

def printall(seq, end='\n'):
    for o in seq:
        print(o, end=end)

_justs = {'left': str.ljust, 'right': str.rjust, 'center': str.center,
          '<': str.ljust, '>': str.rjust, '^': str.center}

def printcols(seq, rows=False, swidth=None, pad=2, just='left'):
    if not swidth:
        swidth, _ = shutil.get_terminal_size()
    just = _justs[just]
    seq = list(map(str, seq))
    if not seq: return
    width = max(map(len, seq))
    ncols = max((swidth + pad) // (width + pad), 1)
    if rows:
        rows = chunk(seq, ncols)
    else:
        nrows = (len(seq)-1) // ncols + 1
        rows = zip(*chunk(seq, nrows, ''))
    for r in rows:
        print((' '*pad).join(just(s, width) for s in r).rstrip())

def print2d(arr, pad=2, just='left'):
    just = _justs[just]
    arr = [[str(o) for o in r] for r in arr]
    if not arr: return
    widths = [max(len(r[i]) for r in arr if i < len(r))
              for i in range(max(map(len, arr)))]
    for r in arr:
        print((' '*pad).join(just(s, w) for s, w in zip(r, widths)).rstrip())


def odict(obj=None):
    if isinstance(obj, str):
        return OrderedDict((k, eval(v, {})) for k, v in
                           re.findall(r'(\w+)\s*=\s*([^,]+)', obj))
    return OrderedDict(obj)

def _is_ordereddict(d):
    if isinstance(d, OrderedDict):
        return True
    if isinstance(d, types.MappingProxyType):
        try: return isinstance(d.copy(), OrderedDict)
        except AttributeError: pass
    return False

def printd(dct):
    if not hasattr(dct, 'keys'):
        dct = dict(dct)
    items = dct.items()
    if _is_ordereddict(dct):
        try: items = sorted(items)
        except TypeError: pass
    ksize = max(len(str(k)) for k in dct.keys())
    for k, v in items:
        rep = repr(v)
        sep = '\n' if '\n' in rep else ' '
        print(str(k).ljust(ksize) + ' =', rep, sep=sep)


@pipe
def rdict(dct):
    if _is_ordereddict(dct):
        return OrderedDict((v, k) for k, v in dct.items())
    return {v: k for k, v in dct.items()}

def dfind(dct, val):
    return {k for k, v in dct.items() if v == val}

def anames(obj, val):
    try:
        return dfind(vars(obj), val)
    except TypeError:
        return {n for n in dir(obj) if getattr(obj, n) == val}

def aname(obj, val):
    names = anames(obj, val)
    if names: return names.pop()

def dfilter(dct, cond=None, typ=None):
    cond = cond or bool
    if typ:
        cond = lambda v: isinstance(v, typ)
    return {k: v for k, v in dct.items() if cond(v)}

def dkfilter(dct, cond=None):
    cond = cond or bool
    return {k: v for k, v in dct.items() if cond(k)}

def dmap(dct, func):
    return dict(func(k, v) for k, v in dct.items())

def dkmap(dct, func):
    return {func(k): v for k, v in dct.items()}

def dvmap(dct, func):
    return {k: func(v) for k, v in dct.items()}

def subdict(dct, keys):
    return {k: v for k, v in dct.items() if k in keys}

def ddiff(dct, exclude):
    return {k: v for k, v in dct.items() if k not in exclude}

def dunion(dct1, dct2):
    dct = dct1.copy()
    dct.update(dct2)
    return dct

def dsearch(dct, s):
    if isinstance(dct, types.ModuleType): dct = vars(dct)
    return {k: v for k, v in dct.items() if re.search(s, k, re.IGNORECASE)}

def dvsearch(dct, s):
    if isinstance(dct, types.ModuleType): dct = vars(dct)
    return {k: v for k, v in dct.items() if re.search(s, v, re.IGNORECASE)}

@pipe
def dsort(dct, key=None):
    return OrderedDict(sorted(dct.items(), key=key))

@pipe
def dvsort(dct, key=None):
    key = key or ident
    return OrderedDict(sorted(dct.items(), key=lambda i: key(i[1])))

def search(seq, s):
    if isinstance(seq, types.ModuleType): seq = dir(seq)
    return [s2 for s2 in seq if re.search(s, s2, re.IGNORECASE)]

@pipe
def usfilt(it):
    return lfilter(lambda s: not s.startswith('_'), it)

@pipe
def usdfilt(dct):
    return dkfilter(dct, lambda s: not s.startswith('_'))

def zmap(func, *seqs):
    return (tup + (func(*tup),) for tup in zip(*seqs))
#    return zip(*seqs + (map(func, *seqs),))

def zmaps(seq, *funcs):
    return (tuple([func(x) if func else x for func in funcs]) for x in seqs)
#    return zip(*(map(func, seq) if func else seq for func in funcs))

def dzip(keys, values):
    return dict(zip(keys, values))

def dzmap(func, seq):
    return {k: func(k) for k in seq}
#    return dict(zip(seq, map(func, seq)))

def rzip(*seqs):
    return zip(*map(reversed, seqs))

def renumerate(seq):
    return rzip(range(len(seq)), seq)


def lists(its):
    return [list(it) if isinstance(it, functools2.NonStrIter) else it
            for it in its]


def lwrap(f, name=None):
    def f2(*args, **kwargs):
        return list(f(*args, **kwargs))
    assigned = set(functools.WRAPPER_ASSIGNMENTS) - {'__module__'}
    if name:
        rename(f2, name)
        assigned -= {'__name__', '__qualname__'}
    _update_wrapper(f2, f, assigned, ())
    return f2

##def lwrap_copy(name):
##    def _lwrap_copy(f):
##        f2 = lwrap(f, name)
##        fglobals(1)[name] = f2
##        return f
##    return _lwrap_copy

def lwrap_copy(f, name=None):
    if isinstance(f, str):
        return partial(lwrap_copy, name=f)
    if name is None:
        name = 'l' + f.__name__
    f2 = lwrap(f, name)
    fglobals(1)[name] = f2
    return f

for f in (map, zip, range, filter, reversed, enumerate, islice,
          chunk, schunk, unique, zmap, zmaps, rzip, renumerate):
    lwrap_copy(f)
del f


def xord(c):
    return hex(ord(c))

def escape(s):
    if isinstance(s, bytes):
        s = s.decode('latin-1')
    return s.encode('unicode_escape').decode('ascii')

def unescape(s):
    return s.encode('latin-1', 'backslashreplace').decode('unicode_escape')

def bchr(i):
    return i.to_bytes(1, 'little')
##    return b'%c' % i
##    return chr(i).encode('latin-1')

def bprint(bts):
    if isinstance(bts, int):
        bts = bchr(bts)
    elif isinstance(bts, str):
        bts = bts.encode('latin-1')
    else:
        bts = bytes(bts)
    try:
        sys.stdout.buffer.write(bts + os.linesep.encode())
    except AttributeError:
        print(bts.decode(sys.stdout.encoding, 'ignore'))

@pipe
@autocurrying
def b2s(bts, enc='utf-8'):
    return bts.decode(enc)


def lcm(x, y):
    return abs(x * y) // gcd(x, y)

def sgn(x):
    return x // abs(x or 1)

def cround(z, n=0):
    return complex(round(z.real, n), round(z.imag, n))

@pipe
def thresh(n, p=14):
    if isinstance(n, complex):
        return cround(n, p)
    return round(n, p)


def divmods(x, *divs):
    out = []
    for div in reversed(divs):
        x, m = divmod(x, div)
        out.append(m)
    out.append(x)
    return out[::-1]


def avg(it, *args):
    if args:
        it = (it,) + args
    l = list(it)
    return sum(l) / len(l)

def geom_mean(it, *args):
    if args:
        it = (it,) + args
    l = list(it)
    return reduce(l, operator.mul) ** 1/len(l)

def frac(n, d=None, maxd=1000000):
    if d is not None and isinstance(n, (float, Decimal)):
        d, maxd = None, d
    return Fraction(n, d).limit_denominator(maxd)


def timef(f, *args, **kwargs):
    if isinstance(f, str):
        f = func(f, globs=fglobals(1))
    t=time.perf_counter()
    f(*args, **kwargs)
    return time.perf_counter()-t


class SlicePipe(object):
    def __getitem__(self, item):
        return pipe(operator.itemgetter(item))

sl = SlicePipe()

class IIndexPipe:
    def __getitem__(self, item):
        return pipe(iindex, idx=item)

ii = IIndexPipe()

class VarSetter(object):
    def __getattr__(self, name):
        return pipe(setl, name, depth=1)

v = VarSetter()

c = pipe #call
im = i = pipe(impt, _depth=1)
f = func
l = pipe(list)
ln = pipe(len)
s = pipe(str)
lns = pipe(str.splitlines)
j = pipe(lambda x: ''.join(map(str, x)))
srt = pipe(sorted)
p = cat = pipe(print)
w = pipe(print, end='')
pr = pipe(printr)
bp = pipe(bprint)
bf = lambda bits=8, sign=False, prefix=False: \
     pipe(lambda n: print(binfmt(n, bits, sign, prefix)))
hf = lambda digs=8, sign=False, prefix=False: \
     pipe(lambda n: print(hexfmt(n, digs, sign, prefix)))
pf = lambda p=4: pipe(lambda f: print('%.*g' % (p, f)))
pa = pipe(printall)
wa = pj = pipe(printall, end='')
ps = pipe(printall, end=' ')
pc = pipe(printcols)
pcr = pipe(printcols, rows=True)
p2d = pipe(print2d)
pd = pipe(printd)
hd = lambda n=10, wrap=True: pipe(head, n=n, wrap=wrap)
tl = lambda n=10, wrap=True: pipe(tail, n=n, wrap=wrap)
doc = pipe(inspect.getdoc)
dp = pipe(lambda obj: print(inspect.getdoc(obj)))
sig = pipe(lambda f: print(inspect.signature(f)))
src = pipe(lambda f: print(inspect.getsource(f)))
d = pipe(dir)
vrs = pipe(vars)
tp = pipe(type)
fr = pipe(frac)
enum = pipe(lenumerate)
mp = lambda f: pipe(lmap, f)
stmp = lambda f: pipe(itertools.starmap, f)
flt = lambda f=None: pipe(lfilter, f)
dflt = lambda f=None, typ=None: pipe(dfilter, cond=f, typ=typ)
dkflt = lambda f=None: pipe(dkfilter, cond=f)
dmp = lambda f: pipe(dmap, func=f)
dkmp = lambda f: pipe(dkmap, func=f)
dvmp = lambda f: pipe(dvmap, func=f)
sv = lambda n, v=None: setl(n, v, 1) if v else pipe(setl, n, depth=1)
sch = lambda s: pipe(search, s=s)
dsch = lambda s: pipe(dsearch, s=s)
dvsch = lambda s: pipe(dvsearch, s=s)
ditems = pipe(lambda d: list(d.items()))
dkeys = pipe(lambda d: list(d.keys()))
dvalues = pipe(lambda d: list(d.values()))
try:
    h = pipe(help)
except NameError:
    pass

def rn(obj=None, name=None, qualname=None):
    if obj is None:
        return pipe(rename, name=name, qualname=qualname)
    if name is None and qualname is None:
        return pipe(rename, name=obj, qualname=qualname)
    return rename(obj, name, qualname)

@pipe
def r(*mods):
    return tuple([reload(impt(m, 3)) for m in mods])

@pipe
def ia(*mods, **kwargs): # rel=False, _depth=0
    rel=kwargs.get('rel', False)
    _depth=kwargs.get('_depth', 0)
    mods = mods or (utils,)
    globs = fglobals(_depth + 2)
    mods = tuple([impt(m, _depth + 3) for m in mods])
    for mod in mods:
        if rel: reload(mod)
        exec('from {} import *'.format(mod.__name__), globs)
    return mods

ra = pipe(ia, rel=True, _depth=1)

@pipe
def ic(*objs, **kwargs): # rel=False, _depth=0
    rel=kwargs.get('rel', False)
    _depth=kwargs.get('_depth', 0)
    robjs = []
    globs = fglobals(_depth + 2)
    cache = set()
    for cls in objs:
        cls = impt(cls, _depth + 2)
        if rel:
            mod = sys.modules[cls.__module__]
            if mod not in cache:
                cache.add(reload(mod))
            cls = getattr(mod, cls.__name__)
        globs[cls.__name__] = cls
        robjs.append(cls)
    return robjs

rc = pipe(ic, rel=True, _depth=1)

def clear_vars():
    d = fglobals(1)
    for n in list(d):
        if not re.match(r'^__.*__$', n):
            del d[n]


@pipe
def decomp(o):
    import unpyc3
    print(unpyc3.decompile(o))


def isbuiltinclass(obj):
    if not isinstance(obj, type):
        obj = type(obj)
    return hasattr(sys.modules.get(obj.__module__), '__file__')


def setdisplayhook(func, typ=object):
    global _displayhook
    def displayhook(value):
        if isinstance(value, typ):
            return func(value)
        return _displayhook(value)
    if '_displayhook' not in globals():
        _displayhook = sys.displayhook
    sys.displayhook = displayhook

def resetdisplayhook():
    global _displayhook
    if '_displayhook' in globals():
        sys.displayhook = _displayhook
        del _displayhook


def cls():
    print('\n' * 24)


def cd(path=None):
    if path:
        os.chdir(os.path.expanduser(os.path.expandvars(path)))
    return os.getcwd()





### Module import shortcuts ###

def np():
    import numpy
    exec(pr('import numpy, numpy as np\n'
            'np.set_printoptions(suppress=True)'), fglobals(1))
    return numpy

def qt4():
    from PyQt4 import Qt
    exec(pr('import PyQt4\n'
            'from PyQt4 import QtCore, QtGui, Qt as Q\n'
            'from PyQt4.Qt import *\n'
            'app = QApplication([])'), fglobals(1))
    return Qt

def qt5():
    from PyQt5 import Qt
    exec(pr('import PyQt5\n'
            'from PyQt5 import QtCore, QtGui, QtWidgets, Qt as Q\n'
            'from PyQt5.Qt import *\n'
            'app = QApplication([])'), fglobals(1))
    return Qt

def mpl(interactive=True):
    import matplotlib
    exec(pr('import matplotlib as mpl\n'
            'import matplotlib.pyplot as plt'
            + ('\nplt.ion()' if interactive else '')),
         fglobals(1))
    return matplotlib

def pylab(interactive=True):
    import pylab
    exec(pr('from pylab import *'
            + ('\nion()' if interactive else '')),
         fglobals(1))
    return pylab

def pylab3d():
    import pylab
    exec(pr('from pylab import *\n'
            'ion()\n'
            'import mpl_toolkits.mplot3d\n'
            "ax = subplot(111, projection='3d')"), fglobals(1))
    return pylab

def sympy():
    import sympy
    exec(pr('import sympy, sympy as sp; from sympy import *\n'
            'R = Rational\n'
            'var("x, y, z, a, b, c, t")'),
         fglobals(1))
    return sympy

def scipy():
    import scipy
    exec(pr('import scipy, scipy as sp\n'
            'import scipy.misc, scipy.special, scipy.ndimage, '
            'scipy.integrate, scipy.signal'), fglobals(1))
    return scipy

def pygame(init=True):
    import pygame
    exec(pr('import pygame, pygame as pg\n'
            'from pygame.locals import *'
            + ('\npygame.init()' if init else '')),
         fglobals(1))
    return pygame

def PIL():
    import PIL.Image
    exec(pr('import PIL; from PIL import Image'), fglobals(1))
    return PIL

def ctypes():
    import ctypes
    exec(pr('''\
import ctypes; from ctypes import *
from ctypes.util import *
try: from ctypes.wintypes import *
except: pass
try: libc = cdll.msvcrt
except: libc = CDLL(find_library('c'))'''), fglobals(1))
    return ctypes

def requests():
    import requests
    exec(pr('import requests'), fglobals(1))
    return requests

def pandas():
    import pandas
    exec(pr('import pandas as pd'), fglobals(1))
    return pandas


def qenum_name(x):
    if 'PyQt4' in sys.modules:
        import PyQt4
    if 'PyQt5' in sys.modules:
        import PyQt5
    tp = type(x)
    pname = tp.__module__ + '.' + tp.__qualname__.rsplit('.', 1)[0]
    pname = re.sub(r'\bphonon\b(?!\.Phonon)', 'phonon.Phonon', pname)
    pclass = eval(pname)
    for n, v in vars(pclass).items():
        if type(v) is tp and v == x:
            return n
    return None


def readrows(typ=int, file=None):
    file = open(file) if file else sys.stdin
    return [list(map(typ, s.split())) for s in
            itertools.takewhile(str.strip, file)]

def readcols(typ=int, file=None):
    return list(map(list, zip(*readrows(typ, file))))


def ipy_resize(w=None):
    import shutil, IPython
    if not w:
        w, _ = shutil.get_terminal_size()
    config = IPython.get_ipython().config
    config.PlainTextFormatter.max_width = w - 8
    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    shell.init_display_formatter()


def getdefault(seq, i, default=None):
    try:
        return seq[i]
    except LookupError:
        return default

def unpackdefs(seq, defaults=None, num=None):
    if num is not None:
        defaults = itertools.repeat(defaults, num)
    if defaults is None:
        raise ValueError('must provide defaults or num')
    sentinel = object()
    return [x if x is not sentinel else d for x, d in
            itertools.zip_longest(seq, defaults, fillvalue=sentinel)]


def unpackdict(dct, keys, defaults=None, default=_empty, rest=False):
    keys = list(keys)
    vals = []
    if defaults and not isinstance(defaults, dict):
        defaults = {k: d for k, d in zip(keys, defaults)}
    for k in keys:
        try:
            val = dct[k]
        except KeyError:
            if defaults and k in defaults:
                val = defaults[k]
            elif default is not _empty:
                val = default
            else:
                raise
        vals.append(val)
    if rest:
        keys = set(keys)
        vals.append({k: v for k, v in dct.items() if k not in keys})
    return vals


def default(obj, default):
    return obj if obj is not None else default


def one_or_empty(arg, cond=None):
    if callable(cond):
        cond = cond(arg)
    elif cond is None:
        cond = arg is not None
    return (arg,) if cond else ()


def setdefaults(dct, defaults):
    for k, v in defaults.items():
        dct.setdefault(k, v)


def multimap(seq, funcs):
    return [f(o) for f, o in zip(funcs, seq)]


def multidict(items):
    d = {}
    for k, v in items:
        d.setdefault(k, []).append(v)
    return d


@pipe
def stepiter(it):
    for x in it:
        if input(x) == 'q':
            break


def execfile(file):
    if isinstance(file, str):
        file = open('file', encoding='utf-8')
    exec(compile(file.read(), file.name(), 'exec'))


@pipe
def thousands(n):
    return format(n, '_')


def prunicode(s):
    printall(map(trywrap(unicodedata.name), s))


def irange(start, stop):
    return range(start, stop + 1)


def nospace(s):
    return ''.join(s.split())


def compiles(s, mode=None):
    if mode is None:
        try:
            return compile(s, '<string>', 'eval')
        except SyntaxError:
            return compile(s, '<string>', 'exec')
    return compile(s, '<string>', mode)


def frexp2(x):
    m, e = math.frexp(x)
    return m*2, e-1


def column(a):
    import numpy as np
    return np.asanyarray(a).reshape(-1, 1)


def atleast_col(a):
    import numpy as np
    a = np.asanyarray(a)
    if a.ndim < 2:
        return a.reshape(-1, 1)
    return a


def probs(a, axis=None):
    import numpy as np
    a = np.asarray(a)
    return a / a.sum(axis=axis)


def unit(v, axis=None):
    import numpy as np
    v = np.asarray(v)
    return v / np.linalg.norm(v, axis=axis)


def eq(a, b=None):
    import numpy as np
    if b is None:
        return np.all(a)
    return np.array_equal(a, b)


def multi_shuffle(*arrs):
    import numpy as np
    inds = np.random.permutation(len(arrs[0]))
    return tuple(np.asarray(arr)[inds] for arr in arrs)


##def summer(s=0):
##    def summer(x):
##        nonlocal s
##        s += x
##        return s
##    return summer

class Summer:
    def __init__(self, s=0):
        self.s = s
    def __call__(self, x):
        self.s += x
        return self.s
