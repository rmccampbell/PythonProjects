# -*- coding: utf-8 -*-
from __future__ import print_function, division
del print_function, division

import sys
_PY3 = sys.version_info[0] >= 3

import importlib, warnings

def _try_import(*mods):
    for m in mods:
        try:
            globals()[m] = importlib.import_module(m)
        except (ImportError, SyntaxError) as e:
            warnings.warn('Failed to import %s: %s' % (m, e))

# Builtin imports
import os, collections, functools, itertools, operator, types, math, cmath, re
import io, random, inspect, textwrap, dis, timeit, time, datetime, string
import fractions, decimal, unicodedata, codecs, locale, shutil, numbers
import subprocess, json, base64, copy, hashlib, contextlib, glob, heapq
import struct
import os.path as osp
from math import pi, e, sqrt, exp, log, log10, floor, ceil, factorial, \
     sin, cos, tan, asin, acos, atan, atan2
inf = float('inf')
nan = float('nan')
deg = pi/180
from functools import partial, reduce
from itertools import islice, chain, starmap, count
from collections import OrderedDict, Counter
from fractions import Fraction
from decimal import Decimal
import pprint

if _PY3:
    from itertools import zip_longest
    try: from math import tau
    except ImportError: pass
    try: from math import log2
    except ImportError: pass
    try: from math import gcd
    except ImportError: from fractions import gcd
    try: from importlib import reload
    except ImportError: from imp import reload
    import urllib.request
    from urllib.request import urlopen
    import urllib.parse as urlparse
    _try_import('enum', 'pathlib', 'typing', 'dataclasses')
else:
    from urllib2 import urlopen
    import urlparse

# Allow this module to be symlinked to different names
globals()[__name__] = sys.modules[__name__]

# My imports
import functools2
from functools2 import autocurrying, chunk, comp, ncomp, ident, inv, supply,\
     rpartial, trycall, trywrap, tryiter, iterfunc, unique, is_sorted, ilen,\
     iindex, flatten, deepcopy, deepmap, first, last, unzip, take, pad, window,\
     map2
from functools2 import update_wrapper_signature as _update_wrapper
if _PY3:
    import classes
    from classes import DictNS, Symbol, ReprStr, BinInt, HexInt, PrettyODict
_try_import('misc', 'primes', 'num2words', 'getfiles')

# 3rd Party imports
_try_import('more_itertools')


T, F, N = True, False, None

_empty = functools2.Sentinel('<empty>')


def alias(obj, *names, **kwargs): # _depth=0
    _depth=kwargs.get('_depth', 0)
    if isinstance(obj, str):
        names = (obj,) + names
        return lambda obj: alias(obj, *names, _depth=_depth+1)
    globs = fglobals(_depth+1)
    for name in names:
        globs[name] = obj
    return obj


def lwrap(f, name=None):
    def f2(*args, **kwargs):
        return list(f(*args, **kwargs))
    assigned = set(functools.WRAPPER_ASSIGNMENTS) - {'__module__'}
    if name:
        rename(f2, name)
        assigned -= {'__name__', '__qualname__'}
    _update_wrapper(f2, f, assigned, ())
    return f2

def lwrap_alias(f=None, name=None):
    if f is None or isinstance(f, str):
        return partial(lwrap_alias, name=f or name)
    if name is None:
        name = 'l' + f.__name__
    f2 = lwrap(f, name)
    fglobals(1)[name] = f2
    return f


def flocals(depth=0):
    return sys._getframe(depth + 1).f_locals

def fglobals(depth=0):
    return sys._getframe(depth + 1).f_globals


@alias('c')
class pipe(object):
    def __init__(self, callable_, *args, **kwargs):
        if isinstance(callable_, pipe):
            callable_ = callable_.callable
        if args or kwargs:
            self.callable = partial(callable_, *args, **kwargs)
            self.callable.__doc__ = callable_.__doc__
        else:
            self.callable = callable_

        try:
            _update_wrapper(self, self.callable, updated=())
        except AttributeError:
            _update_wrapper(self, self.callable, ('__doc__',), ())

    def __repr__(self):
        return '<utils.pipe of {!r}>'.format(self.callable)

    def __or__(self, other):
        if isinstance(other, pipe):
            return other.__ror__(self)
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, tuple):
            try:
                res = self.callable(*other)
            except TypeError:
                res = self.callable(other)
        else:
            res = self.callable(other)
        return res

    __lshift__ = __ror__

    def __call__(self, *args, **kwargs):
        res = self.callable(*args, **kwargs)
        if getattr(res, '_autocurrying', False):
            return pipe(res)
        return res

    def __getattr__(self, name):
        return getattr(self.callable, name)

def pipe_alias(f, *names, **kwargs): # __depth
    __depth = kwargs.pop('__depth', 0)
    if isinstance(f, str):
        return rpartial(pipe_alias, f, *names, __depth=__depth+1, **kwargs)
    alias(pipe(f, **kwargs), *names, _depth=__depth+1)
    return f


@alias('f')
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


@pipe_alias('i', 'im', _depth=1)
def autoimport(string, _depth=0):
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


def cblock(code, globs=None, locs=None):
    #can see globals but won't modify them by default
    if globs is None:
        globs = fglobals(1)
    if locs is None:
        locs = {}
    elif locs is True:
        locs = globs
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
            pref = obj.__qualname__.rpartition('.')[0]
            obj.__qualname__ = pref + '.' + name if pref else name
        elif qualname is not False:
            obj.__qualname__ = qualname
    if name is not None:
        obj.__name__ = name
    return obj

def method(cls):
    if not isinstance(cls, type):
        cls = type(cls)
    def method(func):
        func.__qualname__ = cls.__qualname__ + '.' + func.__name__
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
##    loop(map(func, it))
    for x in it:
        func(x)

def getl(name, depth=0):
    return flocals(depth + 1)[name]

def setl(_name=None, _value=None, _depth=0, **kws):
    flocals(_depth + 1).update(kws)
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

@alias('v')
@pipe
def void(*args):
    pass

@alias('clamp')
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
    chrf = bchr if isinstance(c, bytes) else chr
    return chrf(ord(c) - off)

def letters(num=26):
    return ''.join(islice(itertools.cycle(string.ascii_lowercase), num))

@alias('rletters')
def randletters(num=10, mixedcase=False):
    letters = string.ascii_letters if mixedcase else string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(num))

@alias('rwords')
def randwords(num=10, size=10, stdev=1, mixedcase=False):
    return [randletters(max(1, int(random.gauss(size, stdev))), mixedcase)
            for i in range(num)]

def shuffled(it):
    lst = list(it)
    random.shuffle(lst)
    return lst


def randstream(vals):
    if not isinstance(vals, collections.abc.Sequence):
        vals = list(vals)
    while True:
        yield random.choice(vals)


@lwrap
def schunk(s, size=2):
    for i in range(0, len(s), size):
        yield s[i : i+size]

def sgroup(s, size=2, sep=' '):
    if isinstance(s, bytes) and isinstance(sep, str):
        sep = sep.encode()
    return sep.join(schunk(s, size))

@alias('ssplit')
@lwrap
def sbreak(s, *inds):
    prev = 0
    for ind in inds:
        yield s[prev:ind]
        prev = ind
    yield s[prev:]

def ssep(s, inds, sep=' '):
    if isinstance(s, bytes) and isinstance(sep, str):
        sep = sep.encode()
    return sep.join(sbreak(s, *inds))

def sinsert(s, ind, s2):
    return s[:ind] + s2 + s[ind:]

def sdelete(s, ind, ind2=_empty):
    if ind2 is _empty:
        if ind == -1:
            return s[:ind]
        return s[:ind] + s[ind+1:]
    return s[:ind] + s[ind2:]

def sfilter(func, s):
    if not callable(func):
        func = func.__contains__
    return ''.join(filter(func, s))

def smap(func, s):
    return ''.join(map(str, map(func, s)))

def strunc(s, n, suffix='…'):
    return s[:n-len(suffix)] + suffix if len(s) > n else s


def hsplit(string, *inds):
    return list(map('\n'.join,
                    zip(*(sbreak(s, *inds) for s in string.splitlines()))))

def hconcat(*strings):
    line_lists = [s.splitlines() for s in strings]
    widths = [max(map(len, lines)) for lines in line_lists]
    return '\n'.join(
        ''.join(line.ljust(w) for line, w in zip(row, widths))
        for row in zip_longest(*line_lists, fillvalue='')
    )

def vstr(s):
    return '\n'.join(s)

def hpad(s, w, left=False):
    just = str.rjust if left else str.ljust
    return '\n'.join(just(l, w) for l in s.splitlines())

def vpad(s, h, bottom=False):
    padding = '\n' * (h - s.count('\n') - 1)
    return s + padding if bottom else padding + s

@alias('strbin')
def str_bin(s, enc='utf-8', sep=' '):
    if isinstance(s, str):
        s = s.encode(enc)
    return sep.join(map('{:08b}'.format, s))

@alias('strhex')
def str_hex(s, enc=None):
    import binascii
    if isinstance(s, str):
        if enc is None:
            maxc = s and max(s)
            enc = ('latin-1' if maxc <= '\xff' else
                   'utf-16be' if maxc <= '\uffff' else 'utf-32be')
        s = s.encode(enc)
    return binascii.hexlify(s).decode('ascii')

def bytes_frombin(s):
    s = ''.join(s.split())
    n = (len(s) + 7) // 8
    return int(s.ljust(8*n, '0'), 2).to_bytes(n, 'big')
##    return bytes(int(bits, 2) for bits in schunk(''.join(s.split()), 8))

def str_frombin(s, enc='utf-8'):
    return bytes_frombin(s).decode(enc)

def str_fromhex(s, enc='utf-8'):
    return bytes.fromhex(s).decode(enc)

def unsigned(x, n=8):
    return int(x) & (1<<n)-1

def signed(x, n=8):
    sb = 1<<(n-1)
    return (int(x) & (1<<n)-1 ^ sb) - sb

_signed = signed
def tobytes(n, length=None, byteorder=sys.byteorder, signed=False):
    if isinstance(length, str):
        length, byteorder = None, length
    byteorder = {'<': 'little', '>': 'big', '=': sys.byteorder}.get(
        byteorder, byteorder)
    if length is None:
        bl = ((n if n >= 0 else ~n).bit_length() + 1 if signed
              else n.bit_length())
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

@alias('binf')
def binfmt(n, bits=8, sign=False, prefix=False):
    if hasattr(n, 'dtype'):
        bits = n.dtype.itemsize * 8
    pref = '#' if prefix else ''
    prefw = 2 if prefix else 0
    if sign:
        return '{: {}0{}b}'.format(signed(n, bits), pref, prefw+bits+1)
    return '{:{}0{}b}'.format(unsigned(n, bits), pref, prefw+bits)

@alias('hexf')
def hexfmt(n, digs=8, sign=False, prefix=False):
    if hasattr(n, 'dtype'):
        digs = n.dtype.itemsize * 2
    pref = '#' if prefix else ''
    prefw = 2 if prefix else 0
    if sign:
        return '{: {}0{}x}'.format(signed(n, digs*4), pref, prefw+digs+1)
    return '{:{}0{}x}'.format(unsigned(n, digs*4), pref, prefw+digs)

def binint(x):
    return int(x, 2)

def hexint(x):
    return int(x, 16)

def float_binf(num, p=23, pad0=False, prefix=False):
    if not math.isfinite(num):
        return str(num)
    if p is None or p < 0: p = 1074
    sign = '-' if num < 0 else ''
    whole, num = divmod(abs(num), 1)
    ss = [sign, format(int(whole), '#b' if prefix else 'b'), '.']
    for i in range(p):
        if not (num or pad0):
            break
        whole, num = divmod(num*2, 1)
        ss.append('01'[int(whole)])
    return ''.join(ss)

def float_hexf(num, p=13, pad0=False, prefix=False):
    if not math.isfinite(num):
        return str(num)
    if p is None or p < 0: p = 269
    sign = '-' if num < 0 else ''
    whole, num = divmod(abs(num), 1)
    ss = [sign, format(int(whole), '#x' if prefix else 'x'), '.']
    for i in range(p):
        if not (num or pad0):
            break
        whole, num = divmod(num*16, 1)
        ss.append('0123456789abcdef'[int(whole)])
    return ''.join(ss)

def float_bin(num, p=23):
    if p is None or p < 0: p = 52
    s = float(num).hex()
    if '0x' in s:
        i = s.index('.')+1
        j = s.index('p')
        m = int(s[i:j], 16)
        s = s[:i].replace('x', 'b') + binfmt(m, 52)[:p] + s[j:]
    return s

def float_frombin(s):
    s = s.strip()
    m = re.fullmatch(r'((?:0b)?[01]+(?:\.[01]*)?|\.[01]+)(?:p([+-]?\d+))?', s)
    if not m:
        raise ValueError('invalid format')
    s, e = m.groups()
    exp = int(e) if e else 0
    if '.' in s:
        exp -= len(s) - s.index('.') - 1
    return float(int(s.replace('.', '', 1), 2) * 2**exp)


@pipe
def head(s=None, n=10, wrap=80):
    if s is None:
        return pipe(head, n=n, wrap=wrap)
    if isinstance(s, int):
        return pipe(head, n=s, wrap=wrap)
    if wrap:
        s = textwrap.fill(str(s), wrap, replace_whitespace=False)
    print(''.join(s.splitlines(True)[:n]))

@pipe
def tail(s, n=10, wrap=80):
    if s is None:
        return pipe(tail, n=n, wrap=wrap)
    if isinstance(s, int):
        return pipe(tail, n=s, wrap=wrap)
    if wrap:
        s = textwrap.fill(str(s), wrap, replace_whitespace=False)
    print(''.join(s.splitlines(True)[-n:]))

@pipe
def more(s, n=24):
    s = str(s).splitlines(True)
    while s:
        hd, s = s[:n], s[n:]
        print(''.join(hd), end='')
        if s and input().lower() == 'q':
            break

@pipe_alias('pr')
def printr(o):
    print(o)
    return o

@pipe_alias('pa')
@pipe_alias('par', rep=True)
@pipe_alias('pj', 'wa', sep='')
@pipe_alias('ps', sep=' ')
def printall(seq, sep='\n', rep=False):
    for o in seq:
        print(repr(o) if rep else o, end=sep)

_justs = {'left': str.ljust, 'right': str.rjust, 'center': str.center,
          '<': str.ljust, '>': str.rjust, '^': str.center}

@pipe_alias('pc')
@pipe_alias('pcr', rows=True)
def printcols(seq, rows=False, sep='', pad=2, just='left', swidth=None,
              ncols=None):
    if not swidth:
        swidth, _ = shutil.get_terminal_size()
    just = _justs[just]
    seq = list(map(str, seq))
    if not seq: return
    width = max(map(len, seq)) + len(sep)
    if ncols is None:
        ncols = max((swidth - width) // (width + pad) + 1, 1)
    if rows:
        rows = chunk(seq, ncols)
    else:
        nrows = (len(seq) - 1) // ncols + 1
        rows = zip(*chunk(seq, nrows, ''))
    for r in rows:
        print((' ' * pad).join(just(s + sep, width) for s in r).rstrip())

@pipe_alias('p2d')
def print2d(arr, sep='', pad=2, just='left'):
    sep = sep.ljust(pad)
    just = _justs[just]
    arr = [[str(o) for o in r] for r in arr]
    if not arr: return
    widths = [max(len(r[i]) for r in arr if i < len(r))
              for i in range(max(map(len, arr)))]
    for r in arr:
        print(sep.join(just(s, w) for s, w in zip(r, widths)).rstrip())


@pipe
def odict(obj=(), **kwargs):
    if isinstance(obj, str):
        import ast
        return OrderedDict(((k, ast.literal_eval(v)) for k, v in
                            re.findall(r'(\w+)\s*=\s*([^,]+)', obj)), **kwargs)
    return OrderedDict(obj, **kwargs)

def _is_ordereddict(d):
    if isinstance(d, OrderedDict):
        return True
    if isinstance(d, types.MappingProxyType):
        try: return isinstance(d.copy(), OrderedDict)
        except AttributeError: pass
    return False

@pipe_alias('pd')
@alias('printd')
def printdict(dct, sort=True):
    if not hasattr(dct, 'keys'):
        dct = dict(dct)
    if not dct: return
    items = dct.items()
    if sort and not _is_ordereddict(dct):
        try: items = sorted(items)
        except TypeError: pass
    ksize = max(len(str(k)) for k in dct.keys())
    for k, v in items:
        rep = repr(v)
        if '\n' in rep:
            firstline, rest = rep.split('\n', 1)
            rep = firstline + '\n' + textwrap.indent(rest, ' '*(ksize + 3))
        print(str(k).ljust(ksize) + ' = ' + rep)


@pipe
def rdict(dct):
    if _is_ordereddict(dct):
        return OrderedDict((v, k) for k, v in dct.items())
    return {v: k for k, v in dct.items()}

@pipe
def rdictall(dct):
    res = {}
    for k, v in dct.items():
        res.setdefault(v, []).append(k)
    return res

def dfind(dct, val):
    return {k for k, v in dct.items() if v == val}

def anames(obj, val):
    try:
        return dfind(vars(obj), val)
    except TypeError:
        return {n for n in dir(obj) if getattr(obj, n) == val}

def aname(obj, val):
    names = anames(obj, val)
    if names:
        return min(names)

def dfilter(dct, cond):
    return {k: v for k, v in dct.items() if cond(k, v)}

def dkfilter(dct, cond=None):
    cond = cond or bool
    return {k: v for k, v in dct.items() if cond(k)}

def dvfilter(dct, cond=None, typ=None):
    cond = cond or bool
    if typ:
        cond = lambda v: isinstance(v, typ)
    return {k: v for k, v in dct.items() if cond(v)}

def dmap(dct, func):
    return dict(func(k, v) for k, v in dct.items())

def dkmap(dct, func):
    return {func(k): v for k, v in dct.items()}

def dvmap(dct, func):
    return {k: func(v) for k, v in dct.items()}

def subdict(dct, keys):
    keys = set(keys)
    return {k: v for k, v in dct.items() if k in keys}

def ddiff(dct, exclude):
    exclude = set(exclude)
    return {k: v for k, v in dct.items() if k not in exclude}

def dunion(dct1, dct2):
    dct = dct1.copy()
    dct.update(dct2)
    return dct

def dsearch(dct, s, case=False):
    if isinstance(dct, types.ModuleType): dct = vars(dct)
    flags = 0 if case else re.IGNORECASE
    return {k: v for k, v in dct.items() if re.search(s, str(k), flags)}

def dvsearch(dct, s, case=False):
    if isinstance(dct, types.ModuleType): dct = vars(dct)
    flags = 0 if case else re.IGNORECASE
    return {k: v for k, v in dct.items() if re.search(s, str(v), flags)}

@pipe
def dsort(dct, key=None):
    return OrderedDict(sorted(dct.items(), key=key))

@pipe
def dvsort(dct, key=None):
    key = key or ident
    return OrderedDict(sorted(dct.items(), key=lambda i: key(i[1])))

@pipe
def dhead(dct=None, n=10):
    if dct is None:
        return pipe(dhead, n=n)
    if isinstance(dct, int):
        return pipe(dhead, n=dct)
    return dict(islice(dct.items(), n))

def search(seq, s, case=False):
    if isinstance(seq, types.ModuleType): seq = dir(seq)
    flags = 0 if case else re.IGNORECASE
    return [s2 for s2 in seq if re.search(s, str(s2), flags)]

def replace(seq, x, y):
    return [o if o != x else y for o in seq]

@pipe
def usfilt(it):
    return lfilter(lambda s: not s.startswith('_'), it)

@pipe
def usdfilt(dct):
    return dkfilter(dct, lambda s: not s.startswith('_'))

@lwrap_alias
def zmap(func, *seqs):
    return (tup + (func(*tup),) for tup in zip(*seqs))
#    return zip(*seqs + (map(func, *seqs),))

@lwrap_alias
def zmaps(seq, *funcs):
    return (tuple([func(x) if func else x for func in funcs]) for x in seq)
#    return zip(*(map(func, seq) if func else seq for func in funcs))

def dzip(keys, values):
    return dict(zip(keys, values))

def dzmap(func, seq):
    return {k: func(k) for k in seq}
#    return dict(zip(seq, map(func, seq)))

@lwrap_alias
def rzip(*seqs):
    return zip(*map(reversed, seqs))

@lwrap_alias
def renumerate(seq):
    return rzip(range(len(seq)), seq)

@lwrap_alias
def tfilter(typ, seq):
    return (x for x in seq if isinstance(x, typ))

@lwrap_alias
def tfilternot(typ, seq):
    return (x for x in seq if not isinstance(x, typ))


def lists(its):
    return [list(it) for it in its]


for f in (map, zip, range, filter, reversed, enumerate, islice, chunk, window,
          unique, take):
    lwrap_alias(f)
del f


def xord(c):
    return hex(ord(c))

def escape(s):
    if isinstance(s, bytes):
        s = s.decode('latin-1')
    return s.encode('unicode_escape').decode('ascii')

def unescape(s):
    return s.encode('latin-1', 'backslashreplace').decode('unicode_escape')

if not _PY3:
    bchr = chr
elif sys.version_info >= (3, 5):
    def bchr(i):
        return b'%c' % i
else:
    def bchr(i):
        return i.to_bytes(1, 'little')

@pipe_alias('bp')
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

def sign(x):
    return x and (x // abs(x) if isinstance(x, int) else x / abs(x))

def cround(z, n=0):
    return complex(round(z.real, n), round(z.imag, n))

@pipe
def thresh(n, p=12):
    if isinstance(n, (list, tuple)):
        return type(n)(thresh(m, p) for m in n)
    if isinstance(n, complex):
        return cround(n, p) + 0.0
    return round(n, p) + 0.0


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

def geom_avg(it, *args):
    if args:
        it = (it,) + args
    l = list(it)
    return reduce(operator.mul, l) ** (1/len(l))


def prod(x):
    return functools.reduce(operator.mul, x, 1)


def cumsum(it, init=0):
    l = []
    s = init
    for x in it:
        s += x
        l.append(s)
    return l

@lwrap_alias
def accum(func, it, init):
    x = init
    for y in it:
        x = func(x, y)
        yield x

@pipe_alias('fr')
def frac(n, d=None, maxd=1000000):
    if d is not None and isinstance(n, (float, Decimal)):
        d, maxd = None, d
    f = Fraction(n, d)
    return f.limit_denominator(maxd) if maxd else f


def timef(f, *args, **kwargs):
    if isinstance(f, str):
        f = func(f, globs=fglobals(1))
    t=time.perf_counter()
    f(*args, **kwargs)
    return time.perf_counter()-t


try:
    h = pipe(help)
except NameError:
    pass
l = pipe(list)
ln = pipe(len)
s = pipe(str)
lns = pipe(str.splitlines)
j = pipe(lambda x: ''.join(map(str, x)))
srt = pipe(sorted)
p = cat = pipe(print)
pp = pipe(pprint.pp if sys.version_info >= (3, 8) else pprint.pprint)
w = pipe(print, end='')
bf = lambda bits=8, sign=False, prefix=False: \
     pipe(lambda n: print(binfmt(n, bits, sign, prefix)))
hf = lambda digs=8, sign=False, prefix=False: \
     pipe(lambda n: print(hexfmt(n, digs, sign, prefix)))
pf = lambda p=4: pipe(lambda f: print('%.*g' % (p, f)))
hd = lambda n=10, wrap=80: pipe(head, n=n, wrap=wrap)
tl = lambda n=10, wrap=80: pipe(tail, n=n, wrap=wrap)
doc = pipe(inspect.getdoc)
dp = pipe(lambda obj: print(inspect.getdoc(obj)))
sig = pipe(lambda f: print(inspect.signature(f)))
src = pipe(lambda f: print(inspect.getsource(f)))
d = pipe(dir)
vrs = pipe(vars)
tp = pipe(type)
enm = pipe(lenumerate)
mp = lambda f: pipe(lmap, f)
mp2 = lambda f: pipe(map2, f)
stmp = lambda f: pipe(itertools.starmap, f)
flt = lambda f=None: pipe(lfilter, f)
dflt = lambda f=None: pipe(dfilter, cond=f)
dkflt = lambda f=None: pipe(dkfilter, cond=f)
dvflt = lambda f=None, typ=None: pipe(dvfilter, cond=f, typ=typ)
dmp = lambda f: pipe(dmap, func=f)
dkmp = lambda f: pipe(dkmap, func=f)
dvmp = lambda f: pipe(dvmap, func=f)
sch = lambda s, case=False: pipe(search, s=s, case=case)
dsch = lambda s, case=False: pipe(dsearch, s=s, case=case)
dvsch = lambda s, case=False: pipe(dvsearch, s=s, case=case)
dct = pipe(dict)
ditems = pipe(lambda d: list(d.items()))
dkeys = pipe(lambda d: list(d.keys()))
dvalues = pipe(lambda d: list(d.values()))
sa = lambda _name=None, _value=None, **kws: pipe(
    seta, _name=_name, _value=_value, **kws)

def rn(obj=None, name=None, qualname=None):
    if obj is None:
        return pipe(rename, name=name, qualname=qualname)
    if name is None and qualname is None:
        return pipe(rename, name=obj, qualname=qualname)
    return rename(obj, name, qualname)


class SlicePipe(object):
    def __getitem__(self, item):
        return pipe(operator.itemgetter(item))

sl = SlicePipe()

class IIndexPipe(object):
    def __getitem__(self, item):
        return pipe(iindex, idx=item)

ii = IIndexPipe()

class VarSetter(object):
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return pipe(setl, name, _depth=1)
    def __call__(self, n, v=None):
        return setl(n, v, 1) if v else pipe(setl, n, _depth=1)

sv = VarSetter()


@pipe_alias('r')
def reloads(*mods):
    return tuple([reload(autoimport(m, 3)) for m in mods])

@pipe_alias('reloadall', 'ra', rel=True, _depth=1)
@pipe_alias('ia', _depth=1)
def importall(*mods, **kwargs): # rel=False, _depth=0
    rel=kwargs.get('rel', False)
    _depth=kwargs.get('_depth', 0)
    mods = mods or (utils,)
    globs = fglobals(_depth + 1)
    # _depth + 2 because of comprehension
    mods = tuple([autoimport(m, _depth + 2) for m in mods])
    for mod in mods:
        if rel: reload(mod)
        exec('from {} import *'.format(mod.__name__), globs)
    return mods

# reloadall = ra = pipe(importall, rel=True, _depth=1)

@pipe_alias('reloadclass', 'rc', rel=True, _depth=1)
@pipe_alias('ic', _depth=1)
def importclass(*objs, **kwargs): # rel=False, _depth=0
    rel=kwargs.get('rel', False)
    _depth=kwargs.get('_depth', 0)
    robjs = []
    globs = fglobals(_depth + 1)
    cache = set()
    for cls in objs:
        cls = autoimport(cls, _depth + 1)
        if rel:
            mod = sys.modules[cls.__module__]
            if mod not in cache:
                cache.add(reload(mod))
            cls = getattr(mod, cls.__name__)
        globs[cls.__name__] = cls
        robjs.append(cls)
    return robjs

# reloadclass = rc = pipe(importclass, rel=True, _depth=1)

@pipe_alias('ifr', _depth=1)
def importfrom(*mods, **kwargs):
    _depth=kwargs.get('_depth', 0)
    globs = fglobals(_depth + 1)
    # _depth + 2 because of comprehension
    mods = tuple([autoimport(m, _depth + 2) for m in mods])
    for mod in mods:
        globs[mod.__name__.split('.')[-1]] = mod
    return mods


def clear_vars():
    d = fglobals(1)
    for n in list(d):
        if not re.match(r'^__.*__$', n):
            del d[n]


def isbuiltinmod(mod):
    if isinstance(mod, str):
        mod = sys.modules[mod]
    file = getattr(mod, '__file__', None)
    return not file

def isbuiltinclass(obj):
    if not isinstance(obj, type):
        obj = type(obj)
    try:
        obj.__x = None
    except TypeError:
        return True
    else:
        del obj.__x
        return False


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


@pipe
def cd(path=None):
    if path:
        os.chdir(os.path.expanduser(os.path.expandvars(path)))
    return os.getcwd()

ls = pipe(os.listdir)


### Module import shortcuts ###

def _is_autocomplete():
    files = ('autocomplete.py', 'calltip.py', 'rlcompleter.py', 'completer.py',
             'completion.py', 'oinspect.py', 'dir2.py')
    for f in inspect.stack():
        if f[1].lower().endswith(files) or 'inspect' in f[3]:
            return True
##        else:
##            print(f[0])
    return False

def _main_globals():
    return sys.modules['__main__'].__dict__

def _print_exec(s):
    if not _is_autocomplete():
        print(s)
        exec(s, _main_globals())
    return s

class lazy_loader(object):
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self.func(), name)
    def __dir__(self):
        return ['func'] + dir(self.func())


@lazy_loader
def np():
    import numpy
    _print_exec('import numpy, numpy as np\n'
                'import numpy.linalg as LA\n'
                'from numpy import array as A\n'
                'np.set_printoptions(suppress=True)')
    return numpy

def qt4():
    from PyQt4 import Qt
    _print_exec('import PyQt4\n'
                'from PyQt4 import QtCore, QtGui, Qt as Q\n'
                'from PyQt4.Qt import *\n'
                'app = QApplication([])')
    return Qt

def qt5():
    from PyQt5 import Qt
    _print_exec('import PyQt5\n'
                'from PyQt5 import QtCore, QtGui, QtWidgets, Qt as Q\n'
                'from PyQt5.Qt import *\n'
                'app = QApplication([])')
    return Qt

def pyside2():
    import PySide2
    _print_exec('import PySide2\n'
                'from PySide2 import QtCore, QtGui, QtWidgets\n'
                'from PySide2.QtCore import Qt\n'
                'app = QtWidgets.QApplication([])')
    return PySide2

def pyside6():
    import PySide6
    _print_exec('import PySide6\n'
                'from PySide6 import QtCore, QtGui, QtWidgets\n'
                'from PySide6.QtCore import Qt\n'
                'app = QtWidgets.QApplication([])')
    return PySide6

@lazy_loader
def mpl(backend=None, interactive=True):
    if isinstance(backend, (bool, int)):
        backend, interactive = None, backend
    if backend is None and sys.stdout.__class__.__module__ == 'idlelib.run':
        backend = 'QtAgg'
    import matplotlib
    _print_exec('import matplotlib, matplotlib as mpl\n'
                + ('mpl.use({!r})\n'.format(backend) if backend else '') +
                'import matplotlib.pyplot as plt'
                + ('\nplt.ion()' if interactive else ''))
    return matplotlib

@lazy_loader
def plt(backend=None, interactive=True):
    return mpl(backend, interactive).pyplot

def pylab(backend=None, interactive=True):
    if isinstance(backend, (bool, int)):
        backend, interactive = None, backend
    import pylab
    _print_exec(('import matplotlib as mpl\n' +
                 'mpl.use({!r})\n'.format(backend) if backend else '') +
                'from pylab import *'
                + ('\nion()' if interactive else ''))
    return pylab

def mpl3d(backend=None, interactive=True):
    if isinstance(backend, (bool, int)):
        backend, interactive = None, backend
    import matplotlib
    _print_exec('import matplotlib as mpl\n'
                + ('mpl.use({!r})\n'.format(backend) if backend else '') +
                'import matplotlib.pyplot as plt\n'
                + ('plt.ion()\n' if interactive else '') +
                'from mpl_toolkits import mplot3d\n'
                'from mpl_toolkits.mplot3d.art3d import Poly3DCollection\n'
                "ax = plt.subplot(projection='3d')")
    return matplotlib

def pylab3d(backend=None, interactive=True):
    if isinstance(backend, (bool, int)):
        backend, interactive = None, backend
    import pylab
    _print_exec(('import matplotlib as mpl\n' +
                 'mpl.use({!r})\n'.format(backend) if backend else '') +
                'from pylab import *\n'
                + ('ion()\n' if interactive else '') +
                'from mpl_toolkits import mplot3d\n'
                'from mpl_toolkits.mplot3d.art3d import Poly3DCollection\n'
                "ax = subplot(projection='3d')")
    return pylab

def sns():
    import seaborn
    _print_exec('import seaborn, seaborn as sns')
    return seaborn

def sympy(all=False):
    import sympy
    _print_exec('import sympy, sympy as sp\n'
                + ('from sympy import *\n' if all else '') +
                'R = sympy.Rational\n'
                'sympy.var("x, y, z, a, b, c, d, t", real=True)')
    return sympy

def scipy():
    import scipy
    _print_exec(
        'import scipy, scipy as sp\n'
        'import scipy.misc, scipy.special, scipy.ndimage, scipy.sparse, '
        'scipy.integrate, scipy.signal, scipy.constants, scipy.io.wavfile\n'
        'from scipy import stats')
    return scipy

@alias('pg')
def pygame(init=True):
    import pygame
    _print_exec('import pygame, pygame as pg\n'
                'from pygame.locals import *'
                + ('\npygame.init()' if init else ''))
    return pygame

@lazy_loader
def PIL():
    import PIL.Image
    _print_exec('import PIL; from PIL import Image')
    return PIL

@lazy_loader
def Image():
    return PIL().Image

@lazy_loader
def ctypes():
    import ctypes
    _print_exec('import ctypes; from ctypes import *\n'
                'from ctypes.util import *\n'
                + ('from ctypes.wintypes import *\n'
                   'libc = cdll.msvcrt'
                   if os.name == 'nt' else
                   "libc = CDLL(find_library('c'))"))
    return ctypes

@lazy_loader
def requests():
    import requests
    _print_exec('import requests')
    return requests

def pandas():
    import pandas
    _print_exec('import pandas, pandas as pd')
    return pandas

def argparse():
    import argparse
    _print_exec('import argparse\n'
                'p = argparse.ArgumentParser()')
    return argparse

def tf():
    import tensorflow
    _print_exec('import tensorflow as tf')
    return tensorflow

def torch():
    import torch
    _print_exec('import torch, torchvision\n'
                'import torch.utils.data\n'
                'import torch.nn as nn, torch.nn.functional as F\n'
                'from torch import tensor\n'
                'from torchvision import transforms')
    return torch

def Crypto():
    import Crypto
    _print_exec('import Crypto; from Crypto import *\n'
                'from Crypto.Cipher import AES\n'
                'from Crypto.Hash import SHA256\n'
                'from Crypto.Util import Padding\n'
                'from Crypto.Protocol import KDF\n'
                'from Crypto.PublicKey import RSA\n'
                'from Crypto.Cipher import PKCS1_OAEP\n'
                'from Crypto.Signature import pss')
    return Crypto

def OpenGL():
    import OpenGL
    _print_exec('import OpenGL\n'
                'from OpenGL import GL, GLU, GLUT\n'
                'from OpenGL.GL import shaders\n'
                'from OpenGL.arrays.vbo import VBO\n'
                'import glm')
    return OpenGL

@lazy_loader
def bs4():
    import bs4
    _print_exec('import bs4')
    return bs4

def nltk():
    import nltk
    _print_exec('import nltk\n'
                'from nltk.corpus import wordnet\n'
                'wordnet.synset')
    return nltk

def pint():
    import pint
    _print_exec('import pint\n'
                 'ureg = pint.UnitRegistry()\n'
                 'Q_ = ureg.Quantity')
    return pint

def soundfile():
    import soundfile
    _print_exec('import soundfile, soundfile as sf')
    return soundfile

def sounddevice():
    import sounddevice
    _print_exec('import sounddevice, sounddevice as sd')
    return sounddevice


################

def qenum_name(x):
    locs = {m: sys.modules[m]
            for m in ['PyQt4', 'PyQt5', 'PySide2', 'PySide6']
            if m in sys.modules}
    tp = type(x)
    pname = tp.__module__ + '.' + tp.__qualname__.rsplit('.', 1)[0]
    pname = re.sub(r'\bphonon\b(?!\.Phonon)', 'phonon.Phonon', pname)
    pclass = eval(pname, locs)
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
    return w

def np_resize(w=None):
    import shutil, numpy as np
    if not w:
        w, _ = shutil.get_terminal_size()
    np.set_printoptions(linewidth=w)
    return w


def getdefault(seq, i, default=None):
    try:
        return seq[i]
    except LookupError:
        return default

def multiget(seq, inds, default=_empty):
    if default is _empty:
        return [seq[ind] for ind in inds]
    return [getdefault(seq, ind, default) for ind in inds]

def unpack_defaults(seq, defaults=None, num=None):
    if num is not None:
        defaults = itertools.repeat(defaults, num)
    if defaults is None:
        raise ValueError('must provide defaults or num')
    sentinel = object()
    return [x if x is not sentinel else d for x, d in
            itertools.zip_longest(seq, defaults, fillvalue=sentinel)]


def unpack_dict(dct, keys, defaults=None, default=_empty, rest=False):
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
    if cond is None:
        cond = arg is not None
    elif callable(cond):
        cond = cond(arg)
    return (arg,) if cond else ()


def setdefaults(dct, defaults):
    for k, v in defaults.items():
        dct.setdefault(k, v)


def applyseq(funcs, *seqs):
    return [f(*xs) for f, xs in zip(funcs, zip(*seqs))]


def multidict(items):
    d = {}
    for k, v in items:
        d.setdefault(k, []).append(v)
    return d


def step(it):
    try:
        for x in it:
            yield x
            if input() == 'q':
                break
    except (EOFError, KeyboardInterrupt):
        pass


@pipe
def stepiter(it):
    try:
        for x in it:
            if isinstance(x, tuple):
                x = ' '.join(map(str, x))
            if input(x) == 'q':
                break
    except (EOFError, KeyboardInterrupt):
        pass


def execfile(file):
    if isinstance(file, str):
        file = open(file, encoding='utf-8')
    exec(compile(file.read(), file.name(), 'exec'))


@pipe
def thousands(n, sep='_'):
    return format(n, ',').replace(',', sep)


@alias('pu')
@alias('punicode')
@pipe
def prunicode(s):
    for c in s:
        try:
            print(unicodedata.name(c))
        except ValueError:
            print(c.encode('unicode_escape').decode())


def irange(start, stop):
    return range(start, stop + 1)


def nospace(s):
    return ''.join(s.split())


def compiles(s, mode=None, *args, **kwargs):
    if mode is None:
        try:
            return compile(s, '<string>', 'eval', *args, **kwargs)
        except SyntaxError:
            return compile(s, '<string>', 'exec', *args, **kwargs)
    return compile(s, '<string>', mode, *args, **kwargs)


def frexp2(x):
    m, e = math.frexp(x)
    return m*2, e-1

### Numpy utils ###

def column(a):
    import numpy as np
    return np.asanyarray(a).reshape(-1, 1)

def atleast_col(a):
    import numpy as np
    a = np.asanyarray(a)
    if a.ndim < 2:
        return a.reshape(-1, 1)
    return a

def atleast_nd(a, nd, newaxes=0):
    import numpy as np
    a = np.asanyarray(a)
    if isinstance(newaxes, int):
        newaxes = [newaxes] * nd
    elif len(newaxes) < nd:
        newaxes = [newaxes[0]]*(nd - len(newaxes)) + list(newaxes)
    assert len(newaxes) == nd
    while a.ndim < nd:
        a = np.expand_dims(a, newaxes[a.ndim])
    return a


def slc(i):
    return slice(i, i+1 or None)

def row(i):
    return slc(i)

def col(i):
    return (slice(None), slc(i))


def probs(a, axis=None):
    import numpy as np
    a = np.asarray(a)
    return a / a.sum(axis=axis, keepdims=True)


def unit(v, axis=None, ord=2):
    import numpy as np
    v = np.asarray(v)
    return v / np.linalg.norm(v, ord=ord, axis=axis, keepdims=True)


def dot(a, b, axis=-1, keepdims=False):
    import numpy as np
    return np.sum(np.multiply(a, b), axis=axis, keepdims=keepdims)


def eq(a, b=None):
    import numpy as np
    if b is None:
        return np.all(a)
    return np.array_equiv(a, b)


def multi_shuffle(*arrs):
    import numpy as np
    inds = np.random.permutation(len(arrs[0]))
    return tuple(np.asarray(arr)[inds] for arr in arrs)


def geom_mean(a, axis=None, keepdims=None):
    import numpy as np
    if keepdims is None:
        keepdims = np._NoValue
    a = np.asanyarray(a)
    out = np.prod(a, axis, float, keepdims=keepdims)
    n = a.size // out.size
    if n == 2:
        return np.sqrt(out)
    if n == 3:
        return np.cbrt(out)
    return out ** (1/n)


def geom_mean2(a, axis=None, keepdims=None):
    import numpy as np
    if keepdims is None:
        keepdims = np._NoValue
    return np.exp(np.mean(np.log(a), axis=axis, keepdims=keepdims))


##def summer(s=0):
##    def summer(x):
##        nonlocal s
##        s += x
##        return s
##    return summer

class Summer(object):
    def __init__(self, s=0):
        self.s = s
    def __call__(self, x):
        self.s += x
        return self.s


def print_updating(it, delay=1.0, end=None, stream=None):
    if delay:
        it = delay_iter(it, delay, False)
    w = 0
    for x in it:
        print('\b'*w + ' '*w + '\b'*w, end='', file=stream)
        s = str(x)
        w = len(s)
        print(s, end='', flush=True, file=stream)
    print(end=end, file=stream)

def delay_iter(it, delay=1.0, delay_first=False):
    skipfirst = not delay_first
    for x in it:
        if skipfirst:
            skipfirst = False
        else:
            time.sleep(delay)
        yield x


def hang_indent(s, indent=4, width=80):
    if isinstance(indent, int):
        indent = ' '*indent
    n = len(indent)
    lines = textwrap.wrap(s[n:], width=width-n)
    return s[:n] + ('\n' + indent).join(lines)
