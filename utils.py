from __future__ import print_function, division
del print_function, division

import sys
_PY3 = sys.version_info[0] >= 3

import os, collections, functools, itertools, operator, types, math, re
import io, random, inspect, textwrap, dis, timeit, time, datetime, string
import unicodedata
from math import pi, e, sqrt, exp, log, log10, floor, ceil, factorial
from math import sin, cos, tan, asin, acos, atan, atan2
inf = float('inf')
nan = float('nan')
deg = pi/180
from functools import partial, reduce
from itertools import islice, chain, starmap
from collections import OrderedDict
from fractions import Fraction
from decimal import Decimal
if _PY3:
    try: from math import log2
    except ImportError: pass
    try: from importlib import reload
    except ImportError: from imp import reload
    import urllib.request
    from urllib.request import urlopen

import functools2, utils, primes, misc
from functools2 import autocurrying, chunk, comp, ncomp, ident, inv, supply
from functools2 import rpartial, trycall, trywrap, tryiter, iterfunc
from functools2 import is_sorted, iindex, flatten, deepcopy, deepmap
from functools2 import update_wrapper_signature as _update_wrapper
if _PY3:
    import classes
    from classes import DictNS, Symbol, ReprStr, BinInt, HexInt, PrettyODict

T, F = True, False


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
        raise ValueError('Nothing to return')

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
            _update_wrapper(self, callable, ('__doc__',), updated)

    def __repr__(self):
        return '<utils.call of {}>'.format(self.callable)

    def __or__(self, other):
        if isinstance(other, call):
            return other.__ror__(self)

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
        globs = fglobals(1)
    if locs is None:
        locs = {}
    if isinstance(code, str):
        code = textwrap.dedent(code)
    exec(code, globs, locs)
    return locs

def rename(obj, name, qualname=None):
    if name is None and qualname in (None, True, False):
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

@call
def loop(it):
    for i in it:
        pass

def each(func):
    return call(lambda it: loop(map(func, it)))

def getl(n, depth=0):
    return flocals(depth+1)[n]

def setl(n, v, depth=0):
    flocals(depth+1)[n] = v
    return v

def setls(_depth=0, **kws):
    flocals(_depth+1).update(kws)

def setg(n, v, depth=0):
    fglobals(depth+1)[n] = v
    return v

def setgs(_depth=0, **kws):
    fglobals(_depth+1).update(kws)

def seta(o, n=None, v=None, **kws):
    if n is not None:
        setattr(o, n, v)
    for n, v in kws.items():
        setattr(o, n, v)
    return o

@call
def void(*args):
    pass

def clip(n, low, high):
    return min(max(n, low), high)

def rints(size=10, max=10):
    return [random.randrange(max) for i in range(size)]
randlist = rints

def crange(start, stop, inclusive=True, nonchars=False):
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

def letters(num=26):
    return ''.join(islice(itertools.cycle(string.ascii_lowercase), num))

def rletters(num=10):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(num))

def rwords(num=10, size=10, stdev=1):
    return [rletters(max(1, int(random.gauss(size, stdev))))
            for i in range(num)]

def shuffled(it):
    lst = list(it)
    random.shuffle(lst)
    return lst

def schunk(s, size=2):
    for i in range(0, len(s), size):
        yield s[i : i+size]
##    return map(''.join, chunk(s, size, dofill=False))

def lschunk(s, size=2):
    return list(schunk(s, size))

def sbreak(s, size=2, c=None):
    if c is None: c = ' ' if isinstance(s, str) else b' '
    return c.join(schunk(s, size))


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

def unsigned(x, n=8):
    return x & (1<<n)-1

def signed(x, n=8):
    return (x & (1<<n)-1) | -(x & 1<<(n-1))

def binfmt(n, bits=8, sign=False, prefix=False):
    if hasattr(n, 'dtype'):
        bits = n.dtype.itemsize * 8
    if sign:
        return '{: 0{}b}'.format(signed(n, bits), bits+1)
    return '{:0{}b}'.format(unsigned(n, bits), bits)

def hexfmt(n, digs=8, sign=False, prefix=False):
    if hasattr(n, 'dtype'):
        digs = n.dtype.itemsize * 2
    if sign:
        return '{: 0{}x}'.format(signed(n, digs*4), digs+1)
    return '{:0{}x}'.format(unsigned(n, digs*4), digs)

def float_bin(num, p=23):
    if p < 0: p = 52
    s = float(num).hex()
    if '0x' in s:
        i = s.index('.')+1
        j = s.index('p')
        m = int(s[i:j], 16)
        s = s[:i].replace('x', 'b') + binfmt(m, 52)[:p] + s[j:]
    return s

def float_binf(num, p=23, pad0=False, pref=False):
    if p < 0: p = 1074
    num, whole = math.modf(num)
    num = abs(num)
    ss = [format(int(whole), '#b' if pref else 'b'), '.']
    #ss = ['{:{}b}.'.format(int(whole), '#' if pref else '')]
    for i in range(p):
        if not (num or pad0):
            break
        num *= 2
        num, whole = math.modf(num)
        ss.append('01'[int(whole)])
    return ''.join(ss)

def float_frombin(s):
    s = s.strip()
    if re.search(r'\s', s):
        raise ValueError('invalid format')
    s, p, e = s.lower().partition('p')
    exp = int(e) if p else 0
    if '.' in s:
        exp -= len(s) - s.index('.') - 1
    return float(int(s.replace('.', '', 1), 2) * 2**exp)

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

_justs = {'left': str.ljust, 'right': str.rjust, 'center': str.center}
def printcols(seq, rows=False, swidth=80, pad=2, just='left'):
    just = _justs[just]
    seq = list(map(str, seq))
    if not seq: return
    width = max(map(len, seq))
    ncols = max((swidth + pad) // (width + pad), 1)
    if rows:
        rows = chunk(seq, ncols, '')
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


@call
def rdict(dct):
    if _is_ordereddict(dct):
        return OrderedDict((v, k) for k, v in dct.items())
    return {v: k for k, v in dct.items()}

def dfind(dct, val):
    return {k for k, v in dct.items() if v == val}

def anames(obj, val):
    return dfind(vars(obj), val)

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

def dvals(dct, keys):
    return [dct[k] for k in keys]

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

@call
def dsort(dct, key=None):
    return OrderedDict(sorted(dct.items(), key=key))

@call
def dvsort(dct, key=None):
    key = key or ident
    return OrderedDict(sorted(dct.items(), key=lambda i: key(i[1])))

def search(seq, s):
    if isinstance(seq, types.ModuleType): seq = dir(seq)
    return [s2 for s2 in seq if re.search(s, s2, re.IGNORECASE)]

@call
def ufilt(it):
    return lfilter(lambda s: not s.startswith('_'), it)

@call
def udfilt(dct):
    return dkfilter(dct, lambda s: not s.startswith('_'))

def zmap(func, *seqs):
    return zip(*seqs + (map(func, *seqs),))

def dzmap(func, seq):
    return dict(zip(seq, map(func, seq)))

def zmaps(seq, *funcs):
    return zip(*(map(func, seq) if func else seq for func in funcs))

def rzip(*seqs):
    return zip(*map(reversed, seqs))

def renumerate(seq):
    return rzip(range(len(seq)), seq)


def lwrap(f, name=None):
    def f2(*args, **kwargs):
        return list(f(*args, **kwargs))
    assigned = set(functools.WRAPPER_ASSIGNMENTS) - {'__module__'}
    _update_wrapper(f2, f, assigned, ())
    if name:
        f2 = rename(f2, name)
    return f2

def lwrap_copy(name):
    def _lwrap_copy(f):
        f2 = lwrap(f, name)
        fglobals(1)[name] = f2
        return f
    return _lwrap_copy

for f in map, zip, range, filter, reversed, enumerate:
    name = 'l' + f.__name__
    globals()[name] = lwrap(f, name)
del f, name

lchunk = lwrap(chunk, 'lchunk')


def xord(c):
    return hex(ord(c))

def escape(s):
    return s.encode('unicode_escape').decode('ascii')

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
        sys.stdout.buffer.write(bts + b'\n')
    except AttributeError:
        print(bts.decode(sys.stdout.encoding, 'ignore'))

@call
@autocurrying
def b2s(bts, enc='utf-8'):
    return bts.decode(enc)


def cround(z, n=0):
    return complex(round(z.real, n), round(z.imag, n))

@call
def thresh(n):
    if isinstance(n, complex):
        return cround(n, 15)
    return round(n, 15)

def timef(f, *args):
    if isinstance(f, str):
        f = func(f, globs=fglobals(1))
    t=time.perf_counter()
    f(*args)
    print(time.perf_counter()-t)


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
except NameError:
    pass
l = call(list)
ln = call(len)
s = call(str)
lns = call(str.splitlines)
j = call(lambda x: ''.join(map(str, x)))
srt = call(sorted)
p = cat = call(print)
w = call(print, end='')
pr = call(printr)
bp = call(bprint)
bf = lambda bits=8, sign=False: call(lambda n: print(binfmt(n, bits, sign)))
hf = lambda digs=8, sign=False: call(lambda n: print(hexfmt(n, digs, sign)))
pf = lambda p=4: call(lambda f: print('%.*g' % (p, f)))
pa = call(printall)
pj = call(printall, end='')
ps = call(printall, end=' ')
pc = call(printcols)
pcr = call(printcols, rows=True)
p2d = call(print2d)
pd = call(printd)
hd = lambda n=10, wrap=True: call(head, n=n, wrap=wrap)
tl = lambda n=10, wrap=True: call(tail, n=n, wrap=wrap)
doc = call(inspect.getdoc)
dp = call(lambda obj: print(inspect.getdoc(obj)))
sig = call(lambda f: print(inspect.signature(f)))
src = call(lambda f: print(inspect.getsource(f)))
d = call(dir)
vrs = call(vars)
t = call(type, wrapcall=False)
tm = call(timef)
fr = call(lambda *args: Fraction(*args).limit_denominator())
mp = lambda f: call(lmap, f)
stmp = lambda f: call(itertools.starmap, f)
flt = lambda f=None: call(lfilter, f)
dflt = lambda f=None, typ=None: call(dfilter, cond=f, typ=typ)
dkflt = lambda f=None: call(dkfilter, cond=f)
dmp = lambda f: call(dmap, func=f)
dkmp = lambda f: call(dkmap, func=f)
dvmp = lambda f: call(dvmap, func=f)
sv = lambda n, v=None: setl(n, v, 1) if v else call(setl, n, depth=1)
sch = lambda s: call(search, s=s)
dsch = lambda s: call(dsearch, s=s)
ditems = call(lambda d: list(d.items()))
dkeys = call(lambda d: list(d.keys()))
dvalues = call(lambda d: list(d.values()))

@call
def r(*mods):
    return tuple([reload(impt(m, 3)) for m in mods])

@call
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

ri = ra = call(ia, rel=True, _depth=1)

@call
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

rc = call(ic, rel=True, _depth=1)

def clear():
    d = fglobals(1)
    for n in list(d):
        if not re.match(r'^__.*__$', n):
            del d[n]


@call
def decomp(o):
    import unpyc3
    print(unpyc3.decompile(o))


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


def np():
    import numpy
    exec(pr('import numpy, numpy as np'), fglobals(1))
    return numpy

def qt():
    from PyQt4 import Qt
    exec(pr('import PyQt4\n'
            'from PyQt4 import QtCore, QtGui, Qt as Q\n'
            'from PyQt4.Qt import *\n'
            'app = QApplication([])'), fglobals(1))
    return Qt

def plt():
    from matplotlib import pyplot
    exec(pr('from pylab import *'), fglobals(1))
    return pyplot

def sympy():
    import sympy
    exec(pr('import sympy, sympy as sp; from sympy import *\n'
            'R = Rational\n'
            'var("x, y, z, a, b, c")'),
         fglobals(1))
    return sympy

def scipy():
    import scipy.misc, scipy.special, scipy.ndimage, scipy.integrate, scipy.signal
    exec(pr('import scipy, scipy as sp'), fglobals(1))
    return scipy

def pg():
    import pygame
    pygame.init()
    exec(pr('import pygame, pygame as pg; from pygame.locals import *'),
         fglobals(1))
    return pygame

def PIL():
    import PIL.Image
    exec(pr('import PIL; from PIL import Image'), fglobals(1))
    return PIL

def ctypes():
    import ctypes
    exec(pr('import ctypes; from ctypes import *\n'
            'try: from ctypes.wintypes import *\n'
            'except: pass'), fglobals(1))
    return ctypes


def qenum_name(x):
    import PyQt4.Qt
    tp = type(x)
    pname = tp.__module__ + '.' + tp.__qualname__.rsplit('.', 1)[0]
    pname = re.sub(r'\bphonon\b(?!\.Phonon)', 'phonon.Phonon', pname)
    pclass = eval(pname)
    for n, v in vars(pclass).items():
        if type(v) is tp and v == x:
            return n
    return None

