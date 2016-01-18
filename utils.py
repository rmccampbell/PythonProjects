from __future__ import print_function, division
del print_function, division

import sys, os, collections, functools, itertools, operator, types, math, re
import io, random, inspect, textwrap, dis, timeit, time, string, unicodedata
import functools2, math2, utils
from math import pi, e, sqrt, sin, cos, tan, asin, acos, atan, atan2
from math import floor, ceil
from functools import partial, reduce
from itertools import islice, chain
from collections import OrderedDict
from fractions import Fraction
from decimal import Decimal
try:
    from importlib import reload
except ImportError:
    from imp import reload

from functools2 import autocurrying, chunk, comp, ncomp, ident, inv, supply
from functools2 import is_sorted, iindex, flatten
from functools2 import update_wrapper_signature as _update_wrapper

_PY3 = sys.version_info[0] >= 3

try:
    import classes
    from classes import DictNS, Symbol
except:
    print('"classes" import failed', file=sys.stderr)

def func(code, name=None, globs=None):
    if globs is None:
        globs = sys._getframe(1).f_globals
    if name is None:
        exclude = globs.copy()
    if isinstance(code, str):
        code = textwrap.dedent(code)

    exec(code, globs)
    if name is not None:
        return globs[name]
    else:
        for n, v in globs.items():
            if not n.startswith('_') and (n, v) not in exclude.items():
                return v
        raise ValueError('Nothing to return')

def impt(string, _depth=0):
    globs = sys._getframe(_depth+1).f_locals

    dotnames = re.findall(r'\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', string)
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

class call(object):
    def __init__(self, callable, *args, **kwargs): #wrapcall=True, **kwargs):
        self._wrapcall = kwargs.pop('wrapcall', True) #wrapcall

        if args or kwargs:
            self.callable = partial(callable, *args, **kwargs)
        else:
            self.callable = callable

        if isinstance(callable, (type, call)):
            updated = ()
        else:
            updated = functools.WRAPPER_UPDATES
        try:
            _update_wrapper(self, callable, updated=updated)
        except AttributeError:
            _update_wrapper(self, callable, ('__module__', '__doc__'), updated)

    def __repr__(self):
        return '<utils.call of {}>'.format(self.callable)

    def __or__(self, other):
        if isinstance(other, call):
            return call(comp(self, other))

    def __ror__(self, other):
        if isinstance(other, tuple):
            try:
                res = self.callable(*other)
            except TypeError:
                res = self.callable(other)
        else:
            res = self.callable(other)
        if self._wrapcall and callable(res) and not isinstance(res, call):
            return call(res)
        return res

    def __call__(self, *args, **kwargs):
        res = self.callable(*args, **kwargs)
        if self._wrapcall and callable(res) and not isinstance(res, call):
            return call(res)
        return res

    def __getattr__(self, name):
        return getattr(self.callable, name)

def block(code, globs=None, locs=None):
    #can see globals but won't modify them by default
    if globs is None:
        globs = sys._getframe(1).f_globals
    if locs is None:
        locs = {}
    if isinstance(code, str):
        code = textwrap.dedent(code)
    exec(code, globs, locs)
    return locs

def rename(obj, name, qualname=None):
    if name is None and qualname in (None, True):
        return obj
    if _PY3:
        if qualname is None:
            obj.__qualname__ = name
        elif qualname is True:
            pref = obj.__qualname__.split('.')[:-1]
            obj.__qualname__ = '.'.join(pref + [name])
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

def trycall(func, default=None):
    try:
        return func()
    except:
        return default

def loop(it):
    for i in it:
        pass

def getl(n, depth=0):
    return sys._getframe(depth+1).f_locals[n]

def setl(n, v, depth=0):
    sys._getframe(depth+1).f_locals[n] = v
    return v

def setls(_depth=0, **kws):
    sys._getframe(_depth+1).f_locals.update(kws)

def setg(n, v, depth=0):
    sys._getframe(depth+1).f_globals[n] = v
    return v

def setgs(_depth=0, **kws):
    sys._getframe(_depth+1).f_globals.update(kws)

def seta(o, n, v):
    setattr(o, n, v)
    return o

def setas(o, **kws):
    for n, v in kws.items():
        setattr(o, n, v)
    return o

@call
def void(*args):
    pass

def randlist(size=10, max=10):
    return [random.randrange(max) for i in range(size)]

def crange(start, stop, nonchars=False):
    return ''.join([c for c in map(chr, range(ord(start), ord(stop)+1))
                    if nonchars or unicodedata.category(c) != 'Cn'])

def letters(num=26):
    return ''.join(islice(itertools.cycle(string.ascii_lowercase), num))

def rletters(num=10):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(num))

def rwords(num=10, size=10, stdev=0):
    return [rletters(max(1, int(random.gauss(size, stdev))))
            for i in range(num)]

def schunk(s, size=2):
    for i in range(0, len(s), size):
        yield s[i : i+size]
##    return map(''.join, chunk(s, size, dofill=False))

def sbreak(s, size=2, c=None):
    if c is None: c = ' ' if isinstance(s, str) else b' '
    return c.join(schunk(s))


def strbin(s, enc='utf-8'):
    if isinstance(s, str):
        s = s.encode(enc)
    return ' '.join(map('{:08b}'.format, s))

def strhex(s, enc=None):
    import binascii
    if isinstance(s, str):
        if enc:
            s = s.encode(enc)
        else:
            for enc in ('latin1', 'utf-16be', 'utf-32be'):
                try:
                    s = s.encode(enc)
                except UnicodeEncodeError:
                    pass
    return binascii.hexlify(s).decode('ascii')

def binfmt(n, bits=8):
    if hasattr(n, 'dtype'):
        n, bits = int(n), n.dtype.itemsize * 8
    return format(unsigned(n, bits), '0%db' % bits)

def hexfmt(n, digs=8, sign=False):
    if hasattr(n, 'dtype'):
        n, digs = int(n), n.dtype.itemsize * 2
    if sign:
        return format(signed(n, digs*4), ' 0%dx' % (digs+1))
    return format(unsigned(n, digs*4), '0%dx' % digs)

def unsigned(x, n=8):
    return x & (1<<n)-1

def signed(x, n=8):
    return (x + (1 << n-1) & (1<<n)-1) - (1 << n-1)
##    return x - (1<<n) if x & (1<<(n-1)) else x

def nthbit(x, n):
    return x >> n & 1

def rbits(x, n=8):
	r = 0
	for i in range(n):
		r <<= 1
		r |= x & 1
		x >>= 1
	return r

def float_bin(num, p=20, trim0=True):
    sign = '-' if num < 0 else ''
    num = abs(num)
    whole = int(num)
    num -= whole
    s = sign + bin(whole)[2:] + '.'
    for i in range(p):
        if trim0 and not num:
            break
        num *= 2
        whole = int(num)
        s += str(whole)
        num -= whole
    return s

def float_from_bin(s):
    s = s.strip()
    if re.search(r'\s', s):
        raise ValueError('invalid format')
    s, p, e = s.lower().partition('p')
    exp = int(e) if p else 0
    if '.' in s:
        exp += s.index('.') - len(s) + 1
    return float(int(s.replace('.', '', 1), 2) * 2**exp)

def float_int(num):
    import struct
    return int.from_bytes(struct.pack('>f', num), 'big')

def double_int(num):
    import struct
    return int.from_bytes(struct.pack('>d', num), 'big')

def float_rep(num, sep=' '):
    s = '{:032b}'.format(float_int(num))
    return s[:1] + sep + s[1:9] + sep + s[9:]

def double_rep(num, sep=' '):
    s = '{:064b}'.format(double_int(num))
    return s[:1] + sep + s[1:12] + sep + s[12:]

def float_from_rep(s):
    import struct
    if isinstance(s, str): s = int(s.replace(' ', ''), 2)
    return struct.unpack('>f', s.to_bytes(4, 'big'))[0]

def double_from_rep(s):
    import struct
    if isinstance(s, str): s = int(s.replace(' ', ''), 2)
    return struct.unpack('>d', s.to_bytes(8, 'big'))[0]


def head(s, n=10, wrap=True):
    if wrap:
        s = textwrap.fill(str(s), 80, replace_whitespace=False)
    print(''.join(s.splitlines(True)[:n]))

def tail(s, n=10, wrap=True):
    if wrap:
        s = textwrap.fill(str(s), 80, replace_whitespace=False)
    print(''.join(s.splitlines(True)[-n:]))

def printr(o):
    print(o)
    return o

def printall(seq, end='\n'):
    for o in seq:
        print(o, end=end)

def printcols(seq, rows=False, swidth=80, pad=2, just='left'):
    just = {'left': str.ljust, 'right': str.rjust, 'center': str.center}[just]
    seq = list(map(str, seq))
    if not seq: return
    width = max(map(len, seq))
    ncols = max((swidth + pad) // (width + pad), 1)
    if rows:
        rows = chunk(seq, ncols, '')
    else:
        nrows = int(math.ceil(len(seq) / ncols))
        rows = zip(*chunk(seq, nrows, ''))
    print('\n'.join((' '*pad).join(just(s, width) for s in r) for r in rows))

##def print2d(arr2d):
##    for r in arr2d:
##        print('\t'.join(map(str, r)))

def print2d(arr, pad=2):
    arr = [[str(o) for o in r] for r in arr]
    widths = [max(len(r[i]) for r in arr) for i in range(len(arr[0]))]
    for r in arr:
        print((' '*pad).join(s.ljust(widths[i]) for i, s in enumerate(r)))

def _is_ordereddict(d):
    if isinstance(d, OrderedDict):
        return True
    if isinstance(d, types.MappingProxyType):
        try:
            return isinstance(d.copy(), OrderedDict)
        except AttributeError:
            return False
    return False

def printd(dct):
    if not hasattr(dct, 'keys'):
        dct = dict(dct)
    ksize = max(len(str(k)) for k in dct.keys())
    if _is_ordereddict(dct):
        items = dct.items()
    else:
        try:
            items = sorted(dct.items())
        except:
            items = dct.items()
    for k, v in items:
        print(str(k).ljust(ksize) + ' = ' + repr(v))


@call
def rdict(dct):
    if isinstance(dct, OrderedDict):
        return OrderedDict((v, k) for k, v in dct.items())
    return {v: k for k, v in dct.items()}

def dfind(dct, val):
    return [k for k, v in dct.items() if v == val]

def anames(obj, val):
    return dfind(vars(obj), val)

def aname(obj, val):
    names = anames(obj, val)
    if names: return names[0]

def dfilter(dct, cond):
    return {k: v for k, v in dct.items() if cond(v)}

def dkfilter(dct, cond):
    return {k: v for k, v in dct.items() if cond(k)}

def dmap(dct, func):
    return dict(func(k, v) for k, v in dct.items())

def dkmap(dct, func):
    return {func(k): v for k, v in dct.items()}

def dvmap(dct, func):
    return {k: func(v) for k, v in dct.items()}

def subdict(dct, keys):
    return {k: v for k, v in dct.items() if k in keys}

def dsearch(dct, s):
    s = s.lower()
    return {k: v for k, v in dct.items() if s in k.lower()}

@call
def dsort(dct, key=None):
    return OrderedDict(sorted(dct.items()))

@call
def dvsort(dct, key=None):
    key = key or ident
    return OrderedDict(sorted(dct.items(), key=lambda i: key(i[1])))

def search(seq, s):
    s = s.lower()
    return [s2 for s2 in seq if s in s2.lower()]


def timef(f, *args):
    t=time.perf_counter()
    f(*args)
    print(time.perf_counter()-t)


def cround(z, n=0):
    return complex(round(z.real, n), round(z.imag, n))


def rzip(*seqs):
    return zip(*map(reversed, seqs))

def renumerate(seq):
    return rzip(range(len(seq)), seq)


def lwrap(f, name=None, update=True):
    def f2(*args, **kwargs):
        return list(f(*args, **kwargs))
    f2.__doc__ = f.__doc__
    if update:
        _update_wrapper(f2, f)
    f2 = rename(f2, name, True)
    return f2

def lwrap_copy(name, update=True):
    def _lwrap_copy(f):
        f2 = lwrap(f, name, update)
        sys._getframe(1).f_locals[name] = f2
        return f
    return _lwrap_copy

for f in map, zip, range, filter, reversed, enumerate:
    name = 'l' + f.__name__
    globals()[name] = lwrap(f, name, update=False)

lchunk = lwrap(chunk, 'lchunk')


def bchr(i):
    return i.to_bytes(1, 'big')
##    return chr(i).encode('latin-1')

def bprint(bts):
    if isinstance(bts, int):
        bts = bchr(bts)
    elif isinstance(bts, str):
        bts = bts.encode('latin-1')
    else:
        bts = bytes(bts)
    try:
        sys.stdout.buffer.write(bts + '\n')
    except AttributeError:
        print(bts.decode(sys.stdout.encoding))

@call
@autocurrying
def b2s(bts, enc='utf-8'):
    return bts.decode(enc)

class SliceCall(object):
    def __getitem__(self, item):
        return call(operator.itemgetter(item))

sl = SliceCall()

class IIndex:
    def __getitem__(self, item):
        return call(iindex, idx=item)

ii = IIndex()

class VarSetter(object):
    def __getattr__(self, name):
        return call(setl, name, depth=1)

v = VarSetter()

c = call
im = i = call(impt, _depth=1)
f = func

def rn(obj=None, name=None, qualname=None):
    if obj is None:
        return call(rename, name=name, qualname=qualname, wrapcall=False)
    if name is None:
        return call(rename, name=obj, qualname=qualname, wrapcall=False)
    return rename(obj, name, qualname)

try:
    h = call(help)
except:
    pass
l = call(list)
lp = call(loop)
ln = call(len)
s = call(str)
srt = call(sorted)
p = cat = call(print)
w = call(print, end='')
pr = call(printr)
bp = call(bprint)
bf = lambda bits=8: call(lambda n: print(binfmt(n, bits)))
hf = lambda digs=8, sign=False: call(lambda n: print(hexfmt(n, digs, sign)))
pf = lambda p=4: call(lambda f: print('%%.%dg' % p % f))
pa = call(printall)
pj = call(printall, end='')
pc = call(printcols)
pcr = call(printcols, rows=True)
p2d = call(print2d)
pd = call(printd)
hd = lambda n=10, wrap=True: call(head, n=n, wrap=wrap)
tl = lambda n=10, wrap=True: call(tail, n=n, wrap=wrap)
doc = call(rename(lambda obj: inspect.getdoc(obj), 'doc'))
src = call(lambda f: print(inspect.getsource(f)))
dp = call(lambda obj: print(inspect.getdoc(obj)))
psrc = call(lambda obj: print(inspect.getsource(obj)))
d = call(dir)
t = call(type, wrapcall=False)
tm = call(timef)
fr = call(lambda *args: Fraction(*args).limit_denominator())
r = call(rename(lambda *ms: [reload(m) for m in ms], 'r'))
mp = lambda f: call(lmap, f)
flt = lambda f=None: call(lfilter, f)
dflt = lambda f: call(dfilter, cond=f)
dkflt = lambda f: call(dkfilter, cond=f)
dmp = lambda f: call(dmap, func=f)
dkmp = lambda f: call(dkmap, func=f)
dvmp = lambda f: call(dvmap, func=f)
vd = call(void)
sv = lambda n, v=None: setl(n, v, 1) if v else call(setl, n, depth=1)
sch = lambda s: call(search, s=s)
dsch = lambda s: call(dsearch, s=s)
ditems = call(lambda d: list(d.items()))

@call
def ri(*mods):
    mods = mods or (utils,)
    locs = sys._getframe(2).f_locals
    for mod in mods:
        reload(mod)
        exec('from {} import *'.format(mod.__name__), locs)
    return mods

@call
def rc(*classes):
    rclasses = []
    locs = sys._getframe(2).f_locals
    cache = set()
    for cls in classes:
        mod = sys.modules[cls.__module__]
        if mod not in cache:
            cache.add(reload(mod))
        cls = getattr(mod, cls.__name__)
        locs[cls.__name__] = cls
        rclasses.append(cls)
    return rclasses

def clear():
    d = sys._getframe(1).f_globals
    for n in list(d):
        if not re.match(r'^__.*__$', n):
            del d[n]


@call
def decomp(o):
    import unpyc3
    print(unpyc3.decompile(o))


def setdisplayhook(type, func):
    global _displayhook
    def displayhook(value):
        if isinstance(value, type):
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

