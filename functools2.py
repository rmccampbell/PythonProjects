#!/usr/bin/env python3
import functools, itertools, inspect, random, threading, time
from functools import partial, total_ordering
from collections import Iterable, Iterator
from itertools import islice, groupby
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


class Marker(object):
    def __init__(self, repr):
        self._repr = repr
    def __repr__(self):
        return self._repr


class NonStrIter(Iterable):
    @classmethod
    def __subclasshook__(cls, C):
        if cls is NonStrIter:
            return (any("__iter__" in B.__dict__ for B in C.__mro__) and
                    not issubclass(C, (str, bytes)))
        return NotImplemented

uncopyable = (Iterator, range, dict, type({}.keys()), type({}.values()),
              type({}.items()))


if hasattr(inspect, 'signature'):
    def update_wrapper_signature(wrapper, wrapped,
                                 assigned=functools.WRAPPER_ASSIGNMENTS,
                                 updated=functools.WRAPPER_UPDATES):
        """Same as functools.update_wrapper, but inserts signature in docstring."""
        functools.update_wrapper(wrapper, wrapped, assigned, updated)
        try:
            sigstr = str(inspect.signature(wrapper))
        except ValueError:
            return wrapper
        if not wrapper.__doc__:
            wrapper.__doc__ = sigstr
        elif not wrapper.__doc__.startswith(sigstr):
            wrapper.__doc__ = sigstr + '\n' + wrapper.__doc__
        return wrapper

    def wraps_signature(wrapped, assigned=functools.WRAPPER_ASSIGNMENTS,
                        updated=functools.WRAPPER_UPDATES):
        """Same as functools.wraps, but inserts signature in docstring."""
        return partial(update_wrapper_signature, wrapped=wrapped,
                                 assigned=assigned, updated=updated)

else:
    update_wrapper_signature, wraps_signature = \
        functools.update_wrapper, functools.wraps


def wrap(func, sig=True):
    """Wrapped function returns func's return value unaltered."""
    return (update_wrapper_signature if sig else functools.update_wrapper)(
        lambda *args, **kwargs: func(*args, **kwargs), func)


def ident(x):
    """Return x."""
    return x

def comp(f, g):
    """Return the function composition g(f(x)). (f is the inner function)"""
    return lambda *args, **kwargs: g(f(*args, **kwargs))

def ncomp(*funcs):
    """Compose multiple functions together, evaluated from left to right."""
    return functools.reduce(comp, funcs)

def supply(x):
    """Return a function that returns x, ignoring arguments."""
    return lambda *args, **kwargs: x

def inv(func):
    """Return a function that returns the boolean inverse of func."""
    return lambda *args, **kwargs: not func(*args, **kwargs)


def rpartial(_func, *args, **kwargs):
    """Bind arguments to the right side of the function."""
    _args, _kwargs = args, kwargs
    def rpartial(*args, **kwargs):
        kwargs2 = _kwargs.copy()
        kwargs2.update(kwargs)
        return _func(*args + _args, **kwargs2)
    rpartial._func = _func
    rpartial.args = args
    rpartial.kwargs = kwargs
    return rpartial


def autocurrying(func): #, reverse=False):
    """Wraps function in functools.partial if not enough arguments supplied"""
##    _partial = rpartial if reverse else partial
    try:
        sig = inspect.signature(func)
    except:
        return func
    required = {n for n, p in sig.parameters.items() if p.default == p.empty
                and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)}
    @wraps_signature(func)
    def curried(*args, **kwargs):
        arguments = sig.bind_partial(*args, **kwargs).arguments
        if required - arguments.keys():
            return autocurrying(partial(func, *args, **kwargs))
        else:
            return func(*args, **kwargs)
    curried._autocurrying = True
    curried.func = func
    return curried
##autocurrying = autocurrying(autocurrying)


@autocurrying
def recursion(func, init, n):
    """Evaluates func recursively n times with initial value. If
    arguments are not supplied, returns a new function accepting remaining args."""
    for i in range(n):
        init = func(init)
    return init

def n_recursion(func, n):
    """Returned function evaluates func recursively a predefined number of
    times"""
    f = lambda x: x
    for i in range(n):
        f = (lambda f: lambda x: func(f(x)))(f)
    return f


def typechecking(func):
    """Wrapped function checks argument and return types based on annotations"""
    from inspect import _empty, _VAR_POSITIONAL, _VAR_KEYWORD
    sig = inspect.signature(func)
    for name, param in sig.parameters.items():
        ann, default = param.annotation, param.default
        if default != _empty and ann != _empty and isinstance(ann, type):
            _check_type(default, ann, name)

    @wraps_signature(func)
    def func2(*args, **kwargs):
        bargs = sig.bind(*args, **kwargs).arguments
        for name, barg in bargs.items():
            param = sig.parameters[name]
            ann = param.annotation
            if ann != _empty and isinstance(ann, type):
                if param.kind == _VAR_POSITIONAL:
                    for arg in barg:
                        _check_type(arg, ann, name)
                elif param.kind == _VAR_KEYWORD:
                    for arg in barg.values():
                        _check_type(arg, ann, name)
                else:
                    _check_type(barg, ann, name)

        result = func(*args, **kwargs)
        ret_ann = sig.return_annotation
        if ret_ann != _empty and isinstance(ret_ann, type):
            _check_type(result, ret_ann, ret=True)

        return result

    func2._typechecking = True
    return func2

def _check_type(val, typ, name=None, ret=False):
    name = repr(name) if name else 'return value' if ret else 'argument'
    if not isinstance(val, typ):
        raise TypeError("{} must be of type {}, not {}".format(
            name, typ.__name__, type(val).__name__))



class FunctionWrapper(object):
    def __init__(self, func):
        self.func=func
        update_wrapper_signature(self, func)
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

class Composable(FunctionWrapper):
    def __mul__(self, other):
        return Composable(comp(other, self))
    def __rmul__(self, other):
        return Composable(comp(self, other))


class Placeholder(object):
    unop = '''\
def __{name}__(self):
    return lambda _: {op} _
'''
    binop = '''\
def __{name}__(self, other):
    if isinstance(other, Placeholder):
        return autocurrying(lambda _1, _2: _1 {op} _2)
    return lambda _: _ {op} other
def __r{name}__(self, other):
    return lambda _: other {op} _
'''
    for name, op in dict(pos='+', neg='-', invert='~').items():
        exec(unop.format(name=name, op=op))
    for name, op in dict(add='+', sub='-', mul='*', truediv='/', floordiv='//',
                         mod='%', pow='**', and_='&', or_='|', xor='^',
                         lshift='<<', rshift='>>').items():
        exec(binop.format(name=name.rstrip('_'), op=op))

_ = Placeholder()


def all_eq(it):
    it = iter(it)
    first = next(it, None)
    return all(o == first for o in it)

##def is_sorted(it):
##    it = iter(it)
##    prev = next(it, None)
##    for o in it:
##        if o < prev:
##            return False
##        prev = o
##    return True

def is_sorted(seq):
    return all(seq[i] <= seq[i+1] for i in range(len(seq) - 1))

def runs(it):
    return ((k, sum(1 for o in g)) for k, g in groupby(it))

def num_runs(it):
    return sum(1 for o in groupby(it))

def num_changes(it):
    return max(0, num_runs(it) - 1)

_none = Marker('<none>')
def chunk(seq, size=2, fill=_none, dofill=True):
    """Groups input iterator into equally sized chunks"""
    it = iter(seq)
    if dofill:
        if fill is _none:
            return zip(*(it,)*size)
        return zip_longest(*(it,)*size, fillvalue=fill)
    return chunk_nofill(seq, size)

def chunk_nofill(seq, size=2):
    it = iter(seq)
    chunk = tuple(islice(it, size))
    while chunk:
        yield chunk
        chunk = tuple(islice(it, size))

def flatten(lst, tp=(list, tuple)):
    tp = tp or NonStrIter
    return [b for a in lst for b in
            (flatten(a, tp) if isinstance(a, tp) else (a,))]

def iflatten(it, tp=NonStrIter):
    return (b for a in it for b in
            (iflatten(a, tp) if isinstance(a, tp) else (a,)))


def binsearch(seq, obj):
    first, last = 0, len(seq)
    while first < last:
        i = (first + last)//2
        obj2 = seq[i]
        if obj2 == obj:
            return i
        elif obj2 < obj:
            first = i+1
        else:
            last = i
    return -1

def binsearch2(seq, obj, first=0, last=None):
    if last is  None:
        last = len(seq)
    if last <= first:
        return -1
    mid = (first + last) // 2
    if obj == seq[mid]:
        return mid
    elif obj < seq[mid]:
        return bin_search2(seq, obj, first, mid)
    else:
        return bin_search2(seq, obj, mid + 1, last)

def insertsort(l):
    for i in range(1, len(l)):
        x = l[i]
        while i and l[i-1] > x:
            l[i] = l[i-1]
            i -= 1
        l[i] = x
    return l

def bubblesort(l):
    for i in reversed(range(1, len(l))):
        for j in range(i):
            if l[j] > l[j+1]:
                l[j], l[j+1] = l[j+1], l[j]
    return l

def mergesort(seq):
    if len(seq) > 1:
        mid = len(seq) // 2
        left = mergesort(seq[:mid])
        right = mergesort(seq[mid:])
        return merge(left, right)
    return seq

def merge(left, right):
    result = []
    i, j = 0, 0
    while i < len(left) and j < len(right):
        if left[i] > right[j]:
            result.append(right[j])
            j += 1
        else:
            result.append(left[i])
            i += 1
    result += left[i:]
    result += right[j:]
    return result

def merge2(left, right, res=None):
    if res is None:
        res = []
    if not left:
        res += right
    elif not right:
        res += left
    else:
        if left[0] <= right[0]:
            res.append(left.pop(0))
        else:
            res.append(right.pop(0))
        merge2(left, right, res)
    return res

def merge3(left, right):
    if not left:
        return right
    elif not right:
        return left
    elif left[0] <= right[0]:
        return [left.pop(0)] + merge(left, right)
    else:
        return [right.pop(0)] + merge(left, right)

##def mergesort2(seq, first=0, last=None):
##    if last is None:
##        last = len(seq)
##    if first < last:
##        mid = (first + last) // 2
##        mergesort2(seq, first, mid)
##        mergesort2(seq, mid+1, last)
##        merge(seq, first, mid, last)
##    return seq

def quicksort(seq):
    if len(seq) > 1:
        pivot = seq[len(seq) // 2]
        less, eq, more = [], [], []
        for o in seq:
            if o < pivot:
                less.append(o)
            elif o > pivot:
                more.append(o)
            else:
                eq.append(o)
        return less + eq + more
    return seq

def quicksort2(array, start=0, end=None):
    if end is None:
        end = len(array)-1
    if start < end:
        pivot = array[(start + end) // 2]
        left = start
        right = end
        while left <= right:
            while array[left] < pivot:
                left += 1
            while array[right] > pivot:
                right -= 1
            if left <= right:
                array[left], array[right] = array[right], array[left]
                left += 1
                right -= 1
        quicksort(array, start, right)
        quicksort(array, left, end)
    return array

def radixsort(lst, d=None):
    if d is None:
        d = -math.floor(max(map(math.log10, lst)))
    if d > 5:
        return insertsort(lst)
    bins = [[] for i in range(10)]
    for o in lst:
        i = int(o * 10**d) % 10
        bins[i].append(o)
    ret = []
    for l in bins:
        if len(l) > 1:
            l = radixsort(l, d+1)
        ret.extend(l)
    return ret

def sleepsort(l):
    l2 = []
    def run(i):
        time.sleep(i)
        l2.append(i)
    for i in l:
        threading.Thread(target=run, args=(i,)).start()
    return l2

def bogosort(l):
    while not is_sorted(l):
        random.shuffle(l)
    return l

def bogo_is_sorted(l):
	if len(l) <= 1:
		return True
	l2 = l[:]
	while True:
		l2[:-1] = bogobogosort(l2[:-1])
		if l2[-1] >= l2[-2]:
			return l2 == l
		random.shuffle(l2)

def bogobogosort(l):
    while not bogo_is_sorted(l):
        random.shuffle(l)
    return l


def deepcopy(lst, tp=(list, tuple), conv=None):
    tp = tp or NonStrIter
    if not isinstance(lst, tp):
        raise TypeError
    c = conv or (type(lst) if not isinstance(lst, uncopyable) else list)
    return c(deepcopy(o, tp, conv) if isinstance(o, tp) else o for o in lst)

def deepmap(func, lst, tp=(list, tuple)):
    tp = tp or NonStrIter
    if not isinstance(lst, tp):
        raise TypeError
    c = type(lst) if not isinstance(lst, uncopyable) else list
    return c(
        deepmap(func, o, tp) if isinstance(o, tp) else func(o) for o in lst)


def iindex(it, idx):
    if isinstance(idx, slice):
        return islice(it, idx.start, idx.stop, idx.step)
    if idx < 0:
        raise IndexError
    it = iter(it)
    try:
        o = next(it)
        for i in range(idx):
            o = next(it)
        return o
    except StopIteration:
        raise IndexError


class loose_compare(object):
    def __init__(self, value):
        self.value = value
    def __eq__(self, other):
        return self.value == other.value
    def __lt__(self, other):
        try:
            return self.value < other.value
        except:
            return False
    def __gt__(self, other):
        try:
            return self.value > other.value
        except:
            return False
    def __le__(self, other):
        try:
            return self.value <= other.value
        except:
            return False
    def __ge__(self, other):
        try:
            return self.value >= other.value
        except:
            return False


@total_ordering
class Last(object):
    def __eq__(self, other):
        return False
    def __gt__(self, other):
        return True
LAST = Last()

@total_ordering
class First(object):
    def __eq__(self, other):
        return False
    def __lt__(self, other):
        return True
FIRST = First()

def nones_last(x):
    return x if x is not None else LAST

def nones_first(x):
    return x if x is not None else FIRST
