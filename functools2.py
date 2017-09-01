import functools, itertools, inspect, random, threading, time
from functools import partial, total_ordering
from collections import Iterable, Iterator
from itertools import islice, groupby, chain, combinations
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


class Sentinel(object):
    def __init__(self, repr):
        self._repr = repr
    def __repr__(self):
        return self._repr

_none = Sentinel('<none>')


class NonStrIter(Iterable):
    @classmethod
    def __subclasshook__(cls, C):
        if cls is NonStrIter:
            return (any("__iter__" in B.__dict__ for B in C.__mro__) and
                    not issubclass(C, (str, bytes, bytearray)))
        return NotImplemented

_copyable = (list, tuple, set, frozenset, bytes, bytearray)


if hasattr(inspect, 'signature'):
    def update_wrapper_signature(wrapper, wrapped,
                                 assigned=functools.WRAPPER_ASSIGNMENTS,
                                 updated=functools.WRAPPER_UPDATES):
        """Same as functools.update_wrapper, but inserts signature in docstring."""
        functools.update_wrapper(wrapper, wrapped, assigned, updated)
        try:
            name = getattr(wrapper, '__name__', '')
            sigstr = name + str(inspect.signature(wrapper))
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


# underscore to prevent collisions with kwargs
def rpartial(func_, *args, **kwargs):
    """Bind arguments to the right side of the function."""
    args1, kwargs1 = args, kwargs
    def rpartial(*args, **kwargs):
        kwargs2 = kwargs1.copy()
        kwargs2.update(kwargs)
        return func_(*args + args1, **kwargs2)
    rpartial.func = func_
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


def repeat(func, init, n):
    """Evaluates func recursively n times with initial value"""
    for i in range(n):
        init = func(init)
    return init

def repeated(func, n):
    """Returned function evaluates func recursively n times"""
    f = lambda x: x
    for i in range(n):
        f = (lambda f: lambda x: func(f(x)))(f)
    return f

def iterfunc(func, init, cond=None, stop=_none):
    cond = cond or bool
    while init != stop if stop is not _none else cond(init):
        yield init
        init = func(init)


def trycall(func, default=None, exc=Exception, args=(), kwargs=None):
    try:
        return func(*args, **(kwargs or {}))
    except exc:
        return default

def trywrap(func, default=None, exc=Exception):
    def f(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exc:
            return default
    return update_wrapper_signature(f, func)


def tryiter(func, exc=Exception):
    try:
        while True:
            yield func()
    except exc:
        pass


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
    del unop, binop, name, op

_ = Placeholder()


def all_eq(it):
    it = iter(it)
    first = next(it, None)
    return all(o == first for o in it)

def is_sorted(seq):
    return all(seq[i] <= seq[i+1] for i in range(len(seq) - 1))

def runs(it):
    return ((k, sum(1 for o in g)) for k, g in groupby(it))

def num_runs(it):
    return sum(1 for o in groupby(it))

def num_changes(it):
    return max(0, num_runs(it) - 1)

def unique(it):
    seen = set()
    seen_add = seen.add
    for x in it:
        if x not in seen:
            seen_add(x)
            yield x

def chunk(seq, size=2, fill=_none, partial=True):
    """Groups input iterator into equally sized chunks"""
    if fill is _none:
        if partial:
            return chunk_partial(seq, size)
        return zip(*(iter(seq),)*size)
    return zip_longest(*(iter(seq),)*size, fillvalue=fill)

def chunk_partial(seq, size=2):
    it = iter(seq)
    chunk = tuple(islice(it, size))
    while chunk:
        yield chunk
        chunk = tuple(islice(it, size))

def iflatten(it, types=NonStrIter):
    types = types or NonStrIter
    return (b for a in it for b in
            (iflatten(a, types) if isinstance(a, types) else (a,)))

def flatten(lst, types=(list, tuple)):
    types = types or NonStrIter
    return [b for a in lst for b in
            (flatten(a, types) if isinstance(a, types) else (a,))]

def deepcopy(lst, types=(list, tuple), copy=None):
    types = types or NonStrIter
    if not isinstance(lst, types):
        return lst
    c = copy or (type(lst) if isinstance(lst, _copyable) else list)
    return c(deepcopy(o, types, conv) for o in lst)

def deepmap(func, lst, types=(list, tuple), copy=None):
    types = types or NonStrIter
    if not isinstance(lst, types):
        return func(lst)
    c = copy or (type(lst) if isinstance(lst, _copyable) else list)
    return c(deepmap(func, o, types) for o in lst)


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
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
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
    if len(seq) <= 1:
        return seq
    pivot = seq[len(seq) // 2]
    less, eq, more = [], [], []
    for o in seq:
        if o < pivot:
            less.append(o)
        elif o > pivot:
            more.append(o)
        else:
            eq.append(o)
    return quicksort(less) + eq + quicksort(more)

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
        quicksort2(array, start, right)
        quicksort2(array, left, end)
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

def distribsort(a):
    a2 = [None]*2*len(a)
    for x in a:
        i = 2*x
        while i < len(a2) and a2[i] is not None and a2[i] <= x:
            i += 1
        while i < len(a2) and a2[i] is not None:
            x, a2[i] = a2[i], x
            i += 1
        if i >= len(a2):
            a2.extend([None]*(i - len(a2) + 2))
        a2[i] = x
    return [x for x in a2 if x is not None]

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


class view:
    def __init__(self, seq, start=0, stop=None, step=1):
        self.seq = seq
        n = len(seq)
        if start < 0:
            start += n
        self.start = min(max(0, start), n)
        if stop is None:
            stop = n
        if stop < 0:
            stop += n
        self.stop = min(max(self.start, stop), n)
        self.step = step
    def __len__(self):
        return (self.stop - self.start - 1) // self.step + 1
    def __iter__(self):
        seq = self.seq
        for i in range(self.start, self.stop, self.step):
            yield seq[i]
    def __getitem__(self, i):
        if isinstance(i, slice):
            return view(self.seq, self.start + self.step*i.start,
                                  self.start + self.step*i.stop,
                                  self.step * i.step)
        if i < 0:
            i += len(self)
        if not 0 <= i < self.stop:
            raise IndexError
        return self.seq[self.start + self.step*i]
    def __repr__(self):
        return '<view({})>'.format(list(self.seq[self.start: self.stop: self.step]))


def ilen(it):
    return sum(1 for x in it)

def iindex(it, idx):
    if isinstance(idx, slice):
        return list(islice(it, idx.start, idx.stop, idx.step))
    if idx < 0:
        raise IndexError
    try:
        return next(islice(it, idx, None))
    except StopIteration:
        raise IndexError


def first(it):
    for x in it:
        return x
    raise IndexError

def last(it):
    empty = True
    for x in it:
        empty = True
    if empty:
        raise IndexError
    return x


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


class reverse_order:
    def __init__(self, obj):
        self._obj = obj
    def __eq__(self, other):
        return self._obj == other._obj
    def __ne__(self, other):
        return self._obj != other._obj
    def __lt__(self, other):
        return self._obj > other._obj
    def __gt__(self, other):
        return self._obj < other._obj
    def __le__(self, other):
        return self._obj >= other._obj
    def __ge__(self, other):
        return self._obj <= other._obj

def reverse_key(key):
    return lambda obj: reverse_order(key(obj))


class CompByKey:
    def __eq__(self, other):
        return self._key() == other
    def __ne__(self, other):
        return self._key() != other
    def __lt__(self, other):
        return self._key() < other
    def __gt__(self, other):
        return self._key() > other
    def __le__(self, other):
        return self._key() <= other
    def __ge__(self, other):
        return self._key() >= other

class CompByCmp:
    def __eq__(self, other):
        return self._cmp(other) == 0
    def __ne__(self, other):
        return self._cmp(other) != 0
    def __lt__(self, other):
        return self._cmp(other) < 0
    def __gt__(self, other):
        return self._cmp(other) > 0
    def __le__(self, other):
        return self._cmp(other) <= 0
    def __ge__(self, other):
        return self._cmp(other) >= 0

def cmp(x, y):
    return -1 if x < y else 1 if x > y else 0

def key_to_cmp(func):
    return lambda x, y: cmp(func(x), func(y))

def count(start=0, stop=None, step=1):
    if stop is None:
        return itertools.count(start, step)
    return range(start, stop, step)

def dovetail_i(n, i):
    l = [0]*n
    for j in range(i.bit_length()):
        if i>>j & 1:
            l[j%n] |= 1<<(j//n)
    return tuple(l)

def dovetail(n, m=None):
    for i in count(0, m):
        yield dovetail_i(n, i)

def dovetail2(n, m=None, lim=None):
    x = 0
    i = 0
    while x != lim and i != m:
        for tup in itertools.product(range(x+1), repeat=n):
            if i == m:
                break
            if max(tup) == x:
                i += 1
                yield tup
        x += 1

def subset_i(i):
    l = []
    for j in range(i.bit_length()):
        if i>>j & 1:
            l.append(j)
    return l

def subsets(m=None):
    for i in count(0, m):
        yield subset_i(i)

def strings(alphabet, n=None, m=None):
    j = 0
    for i in count(0, n):
        for s in itertools.product(alphabet, repeat=i):
            if j == m:
                break
            yield s
            j += 1
        if j == m:
            break

def multisets(m=None):
    for i in count(0, m):
        a, b = dovetail_i(2, i)
        s = subset_i(a)
        b += len(s)
        for ss in itertools.product(s, repeat=b):
            yield ss

##def multiset_i(i):
##    s = subset_i(i)
##    l = []
##    for a in s:
##        b, n = dovetail_i(2, a)
##        l.extend([b]*(n+1))
##    return l
##
##def multisets(m=None):
##    x = 0
##    while m is None or i < m:
##        yield multiset_i(i)
##        x += 1

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
