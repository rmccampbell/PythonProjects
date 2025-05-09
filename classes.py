"""A bunch of classes I made."""

import sys, types, collections, itertools, re, math, operator, inspect
import functools, io, textwrap, enum, reprlib, ctypes
import functools2
from functools2 import typechecking, autocurrying, Sentinel
from collections import OrderedDict, defaultdict
import collections.abc as cabc

_empty = Sentinel('<empty>')


class HashlessMap(cabc.MutableMapping):
    """Input key/value pairs as tuples.

    HashlessMap([('a', 1), ('b', 2)])
    HashlessMap(('a', 1), ('b', 2))
    HashlessMap({'a': 1}, b=2)        -> HashlessMap([('a', 1), ('b', 2)])
    """
    def __init__(self, *args, **kwargs):
        self._keys = []
        self._values = []
        self.update(*args, **kwargs)

    def update(self, *args, **kwargs):
        if len(args) == 1:
            obj = args[0]

            if isinstance(obj, cabc.Mapping):
                items = obj.items()
            elif hasattr(obj, 'keys'):
                items = ((key, obj[key]) for key in obj.keys())
            elif len(obj) == 2:
                try:
                    items = [(key, value) for key, value in obj]
                except (TypeError, ValueError):
                    items = args
            else: items = obj

        else: items = args

        for key, value in itertools.chain(items, kwargs.items()):
            self[key] = value

    def __getitem__(self, key):
        try:
            return self._values[self._keys.index(key)]
        except ValueError:
            raise KeyError('Key not in map.') from None

    def __setitem__(self, key, value):
        try:
            self._values[self._keys.index(key)] = value
        except ValueError:
            self._keys.append(key)
            self._values.append(value)

    def __delitem__(self, key):
        try:
            index = self._keys.index(key)
            del self._keys[index], self._values[index]
        except ValueError:
            raise KeyError('Key not in map.') from None

    def __contains__(self, key):
        return key in self._keys

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        yield from self._keys

    @reprlib.recursive_repr()
    def __repr__(self):
        return 'HashlessMap({})'.format(list(self.items()))

    def __str__(self):
        return '{{{}}}'.format(
            ', '.join('{!r}: {!r}'.format(k, v) for k, v in self.items()))

    def keys(self):
        return HashlessMapKeys(self)

    def items(self):
        return HashlessMapItems(self)

    def values(self):
        return HashlessMapValues(self)

class HashlessMapKeys(cabc.KeysView):
    def __iter__(self):
        yield from self._mapping._keys
    def __contains__(self, key):
        return key in self._mapping._keys
    def __repr__(self):
        return '<{}({})>'.format(type(self).__name__, list(self))

class HashlessMapItems(cabc.ItemsView):
    def __iter__(self):
        yield from zip(self._mapping._keys, self._mapping._values)
    def __repr__(self):
        return '<{}({})>'.format(type(self).__name__, list(self))

class HashlessMapValues(cabc.ValuesView):
    def __iter__(self):
        yield from self._mapping._values
    def __contains__(self, value):
        return value in self._mapping._values
    def __repr__(self):
        return '<{}({})>'.format(type(self).__name__, list(self))



class DictNS(dict):
    """A dictionary useable as a namespace."""
    def __init__(self, *args, **kwargs):
        self.__dict__ = self
        super().__init__(*args, **kwargs)

class DictNS2(dict):
    """Alternate implementation of dictionary namespace."""
    __slots__ = ()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(*e.args) from None
    def __setattr__(self, name, value):
        self[name]=value
    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError as e:
            raise AttributeError(*e.args) from None

    @property
    def __dict__(self):
        return self

class MappingNS(cabc.MutableMapping):
    """A normal object namespace with a mapping interface."""
    def __init__(self, *args, **kwargs):
        vars(self).update(*args, **kwargs)
    def __getitem__(self, name):
        return vars(self)[name]
    def __setitem__(self, name, value):
        vars(self)[name] = value
    def __delitem__(self, name):
        del vars(self)[name]
    def __iter__(self):
        return iter(vars(self))
    def __len__(self):
        return len(vars(self))
    def __repr__(self):
        return repr(vars(self))



class AutoAttr:
    def __getattr__(self, name):
        value = type(self)()
        setattr(self, name, value)
        return value

class AutoDict(dict):
    def __missing__(self, key):
        value = type(self)()
        self[key] = value
        return value

def AutoDefDict(*args, **kwargs):
    return defaultdict(AutoDefDict, *args, **kwargs)

class AutoDictNS(DictNS, AutoDict, AutoAttr):
    pass



def _safe_super(typ, obj):
    return super(typ, obj) if isinstance(obj, typ) else obj

class DotDict(AutoDict):
    def __init__(__self, *args, **kwargs):
        super().__init__()
        __self.update(*args, **kwargs)

    update = cabc.MutableMapping.update

    def __getitem__(self, key):
        return self.get_by_keys(key.split('.'))

    def __setitem__(self, key, value):
        keys = key.split('.')
        dct = self.get_by_keys(keys[:-1])
        _safe_super(__class__, dct).__setitem__(keys[-1], value)

    def __delitem__(self, key):
        keys = key.split('.')
        dct = self.get_by_keys(keys[:-1], False)
        _safe_super(__class__, dct).__delitem__(keys[-1])

    def __contains__(self, key):
        missing = object()
        return self.get_by_keys(key.split('.'), default=missing) is not missing

    def get(self, key, default=None):
        return self.get_by_keys(key.split('.'), default=default)

    def setdefault(self, key, default=None):
        keys = key.split('.')
        dct = self.get_by_keys(keys[:-1])
        return _safe_super(__class__, dct).setdefault(keys[-1], default)

    def pop(self, key, default=_empty):
        if default is not _empty:
            try:
                return self.pop(key)
            except KeyError:
                return default
        keys = key.split('.')
        dct = self.get_by_keys(keys[:-1], False)
        return _safe_super(__class__, dct).pop(keys[-1])

    def get_by_keys(self, keys, create=True, default=_empty):
        if default is not _empty:
            create = False
        value = self
        for key in keys:
            if create or _safe_super(__class__, value).__contains__(key):
                value = _safe_super(__class__, value).__getitem__(key)
            elif default is not _empty:
                return default
            else:
                raise KeyError(key)
        return value

class DotDictNS(DotDict, DictNS, AutoAttr):
    pass



class LazyList(list):
    """List that updates itself lazily from an iterator."""
    def __init__(self, it=()):
        self._iter = iter(it)

    def __iter__(self):
        yield from super().__iter__()
        for obj in self._iter:
            super().append(obj)
            yield obj

    def fill(self):
        for obj in self._iter:
            super().append(obj)

    def fill_to(self, n):
        if n < 0:
            return self.fill()
        m = max(n - len(self), 0)
        for obj in itertools.islice(self._iter, m):
            super().append(obj)

    def __getitem__(self, index):
        self.fill_to(index + 1 if index >= 0 else -1)
        return super().__getitem__(index)

    def __setitem__(self, index, value):
        self.fill_to(index + 1 if index >= 0 else -1)
        super().__setitem__(index, value)

    def __delitem__(self, index):
        self.fill_to(index + 1 if index >= 0 else -1)
        super().__delitem__(index)

    def append(self, object):
        self.fill()
        super().append(object)

    def extend(self, iterable):
        self.fill()
        super().extend(iterable)

    def insert(self, index, object):
        self.fill_to(index)
        super().insert(index, object)

    def pop(self, index=-1):
        self.fill_to(index + 1 if index >= 0 else -1)
        return super().pop(index)



class Caching:
    _cache = {}
    def __new__(cls, key):
        try:
            return cls._cache[key]
        except KeyError:
            inst = super().__new__(cls)
            cls._cache[key] = inst
            return inst



class CustomMagic:
    def __setattr__(self, name, value):
        # if name is a "magic" method
        # and there is not already a property asigned to it
        if re.match(r'^__\w+__$', name) and \
           isinstance(value, types.FunctionType) and \
           not isinstance(getattr(type(self), name, None), property):
            def fget(self):
                return vars(self)[name]
            def fset(self, value):
                vars(self)[name] = value
            def fdel(self):
                del vars(self)[name]
            try:
                setattr(type(self), name, property(fget, fset, fdel))
            except AttributeError: pass
        super().__setattr__(name, value)



### Convert list of bits to int and vice-versa. ###
def int_to_bits(num):
    bits = []
    while num > 0:
        bits.append(num & 1)
        num >>= 1
    bits.reverse()
    return bits

def bits_to_int(bits):
    num = 0
    for bit in bits:
        num = (num << 1) | bool(bit)
    return num

class Bits(cabc.Sequence):
    def __init__(self, value, length=None, endian='big'):
        if isinstance(value, str):
            self.value = int(value, 2)
        if isinstance(value, int):
            if value < 0:
                raise ValueError("unsigned integers only")
            self.value = value
            l = value.bit_length()
        elif isinstance(value, cabc.ByteString):
            self.value = int.from_bytes(value, endian)
            l = 8 * len(value)
        else:
            self.value = 0
            for i, bit in enumerate(value):
                self.value |= bool(bit) << i
            l = len(value)
        self.length = length if length is not None else l

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        l = self.length
        if idx < 0:
            idx += l
        if idx < 0 or idx >= l:
            raise IndexError('bit index out of range')
        return self.value >> idx & 1

    def __setitem__(self, idx, value):
        l = self.length
        if idx < 0:
            idx += l
        if idx < 0 or idx >= l:
            raise IndexError('bit index out of range')
        self.value = self.value & ~(1 << idx) | (value << idx)
        self.value ^= (-value ^ self.value) & (1 << idx)

    def __iter__(self):
        num = self.value
        for i in range(self.length):
            yield num >> i & 1

    def __int__(self):
        return self.value

    def __index__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, Bits):
            return self.value == other.value and self.length == other.length
        return False

    def __repr__(self):
        return 'Bits({})'.format(list(self))



class IterProxy(cabc.Iterable):
    def each(self, attr):
        return type(self)(getattr(obj, attr) for obj in self)

    def __getattr__(self, name):
        return self.each(name)

    def __call__(self, *args, **kwargs):
        return type(self)(obj(*args, **kwargs) for obj in self)

class WrapperProxy(IterProxy):
    def __init__(self, it):
        self._iter = it

    def __iter__(self):
        return iter(self._iter)

    def __getattr__(self, name):
        try:
            return getattr(self._iter, name)
        except AttributeError:
            return self.each(name)
    def __getitem__(self, index):
        if isinstance(index, slice):
            return type(self)(self._iter[index])
        return self._iter[index]
    def __repr__(self):
        return 'WrapperProxy({})'.format(self._iter)

class ListProxy(list, IterProxy):
    def __repr__(self):
        return 'ListProxy({})'.format(super().__repr__())



class PropagatingNone:
    _inst = None
    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst
    def __eq__(self, other):
        return other == None
    def __hash__(self):
        return hash(None)
    def __bool__(self):
        return False
    def __getattr__(self, name):
        return self
    def __call__(self, *args, **kwargs):
        return self

PNone = PropagatingNone()



class FakeFunc:
    def __init__(self, name='', body=None, returnv=None,
                 params=(), defaults=None, starargs=None, starkws=None):
        self.name = name
        self.code = body and compile(body, '<string>', 'exec') or None
        self.returnc = returnv and compile(returnv, '<string>', 'eval') or None
        self.params = tuple(params)
        self.defaults = dict(defaults or {})
        self.starargs = starargs
        self.starkws = starkws

    def __call__(self, *args, **kwargs):
        fargs = {}

        others = args[len(self.params):]
        if self.starargs:
            fargs[self.starargs] = others
        elif others:
            raise TypeError("{} takes at most {} argument(s)".format(
                self.name, len(self.params)-len(self.defaults)))

        otherkws = {k: v for k, v in kwargs.items() if k not in self.params}
        if self.starkws:
            fargs[self.starkws] = otherkws
        elif otherkws:
            raise TypeError("{} doesn't expect keyword argument '{}'".format(
                self.name, list(otherkws)[0]))

        fargs.update(self.defaults)
        fargs.update(zip(self.params, args))
        fargs.update({k: v for k, v in kwargs.items() if k in self.params})
        if fargs.keys() < set(self.params):
            raise TypeError('{} requires at least {} arguments.'.format(
                self.name, len(self.params)-len(self.defaults)))

        if self.code: exec(self.code, globals(), fargs)
        if self.returnc: return eval(self.returnc, globals(), fargs)

## alternative implementation for getting params
##for i, p in enumerate(self.params):
##    try:
##        fargs[p] = kwargs[p]
##    except KeyError:
##        try:
##            fargs[p] = args[i]
##        except IndexError:
##            try:
##                fargs[p] = self.defaults[p]
##            except KeyError:
##                raise TypeError("{} requires at least {} argument(s)."
##     .format(self.name, len(self.params)-len(self.defaults))) from None



class SeqDict(OrderedDict):
    def __getitem__(self, key):
        try:
            key = list(self)[key]
        except TypeError:
            pass
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        try:
            key = list(self)[key]
        except TypeError:
            pass
        super().__setitem__(key, value)

    def __delitem__(self, key):
        try:
            key = list(self)[key]
        except TypeError:
            pass
        super().__delitem__(key)

##    def __init__(self, *args, **kwargs):
##        self._keys = []
##        super().__init__(*args, **kwargs)
##
##    def __getitem__(self, key):
##        try:
##            key = self._keys[key]
##        except TypeError:
##            pass
##        return super().__getitem__(key)
##
##    def __setitem__(self, key, value):
##        try:
##            key = self._keys[key]
##        except TypeError:
##            pass
##        if key not in self:
##            self._keys.append(key)
##        super().__setitem__(key, value)



class methoddescriptor:
    def __init__(self, func):
        self.__func__ = func

    def __get__(self, obj, typ=None):
        if obj: return types.MethodType(self.__func__, obj)
        return self.__func__



class InheritingDictMeta(type):
##    @classmethod
##    def get_prepare_type(cls, typ, typ2):
##        if issubclass(typ, typ2):
##            return typ
##        return type('_CustomDict', (typ, typ2), {})
##    @classmethod
##    def get_prepare_type(cls, curcls, dicttype, *args, **kwargs):
##        dicttype2 = type(super(curcls, cls).__prepare__(*args, **kwargs))
##        if issubclass(dicttype, dicttype2):
##            return dicttype
##        return type('_CustomDict', (dicttype, dicttype2), {})

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        dicttypes = []
        for base in cls.__mro__:
            try:
                typ = vars(base)['_dicttype']
            except KeyError:
                continue
            if typ not in dicttypes:
                dicttypes.append(typ)

        if not dicttypes:
            return {}
        if len(dicttypes) == 1:
            return dicttypes[0]()
        return type('_CustomDict', tuple(dicttypes), {})()



class overloading:
    def __init__(self, *funcs):
        if not funcs: raise TypeError('At least one function required.')
        self.funcs = list(funcs)
        functools2.update_wrapper_signature(self, funcs[0])

    @classmethod
    def auto(cls, func):
        try:
            name = func.__name__
        except AttributeError:
            name = func.__func__.__name__
        clsvars = sys._getframe(1).f_locals
        obj = clsvars.get(name)
        if isinstance(obj, overloading):
            return obj.overload(func)
        return cls(func)

    def overload(self, *funcs):
        if not funcs: raise TypeError('At least one function required.')
        self.funcs += funcs
        return self

    def __call__(self, *args, **kwargs):
        err = None
        for func in self.funcs:
            try:
                return func(*args, **kwargs)
            except TypeError as e:
                err = e
        raise TypeError('No function with matching signature.') from err

    def __get__(self, obj, typ=None):
        return OverloadedMethod(self, obj, typ)

class OverloadedMethod:
    def __init__(self, overloading, obj, typ):
        self.overloading = overloading
        self.funcs = overloading.funcs
        self.obj = obj
        self.typ = typ

    def __call__(self, *args, **kwargs):
        err = None
        for func in self.funcs:
            try:
                return func.__get__(self.obj, self.typ)(*args, **kwargs)
            except TypeError as e:
                err = e
        raise TypeError('No function with matching signature.') from err

class _OverloadingDict(dict):
    def __setitem__(self, key, value):
        if isinstance(value, (types.FunctionType, classmethod, staticmethod)):
            obj = self.get(key)
            if isinstance(obj, overloading):
                value = obj.overload(value)
            else:
                value = overloading(value)
        super().__setitem__(key, value)

class OverloadingMeta(InheritingDictMeta):
    _dicttype = _OverloadingDict

##    @classmethod
##    def __prepare__(cls, name, bases):
##        return cls.get_prepare_type(_OverloadingDict,
##                                    type(super().__prepare__(name, bases)))()

class OverloadingBase(metaclass=OverloadingMeta):
    pass


class _TypeCheckingDict(dict):
    def __setitem__(self, key, value):
        if isinstance(value, types.FunctionType):
            if not hasattr(value, '_typechecking'):
                value = typechecking(value)
        elif isinstance(value, classmethod):
            value = classmethod(typechecking(value.__func__))
        elif isinstance(value, staticmethod):
            value = staticmethod(typechecking(value.__func__))

        super().__setitem__(key, value)

class TypeCheckingMeta(InheritingDictMeta):
    _dicttype = _TypeCheckingDict

##    @classmethod
##    def __prepare__(cls, name, bases):
##        return cls.get_prepare_type(_TypeCheckingDict,
##                                    type(super().__prepare__(name, bases)))()

class TypeCheckingBase(metaclass=TypeCheckingMeta):
    pass


class OverloadingTypeCheckingMeta(TypeCheckingMeta, OverloadingMeta):
    pass

class OverloadingTypeChecking(metaclass=OverloadingTypeCheckingMeta):
    pass



try:
    from implicitself import implicit_self, implicit_this
except ImportError:
    pass
else:
    class _ImplicitSelfDict(dict):
        def __setitem__(self, key, value):
            if isinstance(value, types.FunctionType):
                value = implicit_self(value)
                super().__setitem__(key, value)

    class ImplicitSelfMeta(InheritingDictMeta):
        _dicttype = _ImplicitSelfDict

    ##    @classmethod
    ##    def __prepare__(cls, name, bases):
    ##        return cls.get_prepare_type(__class__, _ImplicitSelfDict, name, bases)()

    class ImplicitSelfBase(metaclass=ImplicitSelfMeta):
        pass


    class _ImplicitThisDict(dict):
        def __setitem__(self, key, value):
            if isinstance(value, types.FunctionType):
                value = implicit_this(value)
                super().__setitem__(key, value)

    class ImplicitThisMeta(InheritingDictMeta):
        _dicttype = _ImplicitThisDict

    ##    @classmethod
    ##    def __prepare__(cls, name, bases):
    ##        return cls.get_prepare_type(__class__, _ImplicitThisDict, name, bases)()

    class ImplicitThisBase(metaclass=ImplicitThisMeta):
        pass


    class JavaClassMeta(ImplicitThisMeta, OverloadingTypeCheckingMeta):
        pass

    class JavaClass(metaclass=JavaClassMeta):
        pass



class AbstractSet:
    def __init__(self, predicate):
        if isinstance(predicate, AbstractSet):
            self.predicate = predicate.predicate
        elif callable(predicate):
            self.predicate = predicate
        elif isinstance(predicate, cabc.Container):
            self.predicate = predicate.__contains__
        else:
            raise TypeError('argument must be callable or container')
    def __contains__(self, obj):
        return self.predicate(obj)
    def __invert__(self):
        pred = self.predicate
        return AbstractSet(lambda obj: not pred(obj))
    def __and__(self, other):
        pred1 = self.predicate
        pred2 = AbstractSet(other).predicate
        return AbstractSet(lambda obj: pred1(obj) and pred2(obj))
    def __or__(self, other):
        pred1 = self.predicate
        pred2 = AbstractSet(other).predicate
        return AbstractSet(lambda obj: pred1(obj) or pred2(obj))
    def __xor__(self, other):
        pred1 = self.predicate
        pred2 = AbstractSet(other).predicate
        return AbstractSet(lambda obj: pred1(obj) ^ pred2(obj))
    def __sub__(self, other):
        pred1 = self.predicate
        pred2 = AbstractSet(other).predicate
        return AbstractSet(lambda obj: pred1(obj) and not pred2(obj))

# The set of all sets not members of themselves
russels_set = AbstractSet(lambda obj: isinstance(obj, cabc.Container)
                          and obj not in obj)



def frange(start, stop=None, step=1):
    if stop is None:
        start, stop = 0, start
    count = start
    while count < stop:
        yield count
        count += step


class FRange(cabc.Sequence):
    def __init__(self, start, stop=None, step=1):
        if stop is None:
            start, stop = 0, start
        self.start, self.stop, self.step = start, stop, step
    def __iter__(self):
        count = 0
        i = self.start
        while i < self.stop:
            yield i
            count += 1
            i = self.start + self.step * count
    def __len__(self):
        return math.ceil((self.stop - self.start) / self.step)
    def __getitem__(self, index):
        if index < 0:
            index += len(self)
        value = self.start + self.step * index
        if value < self.start or value >= self.stop:
            raise IndexError(index)
        return value
    def __contains__(self, value):
        if value < self.start or value >= self.stop:
            return False
        return (value - self.start) % self.step == 0



class FollowDescriptors:
    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if hasattr(type(value), '__get__'):
            return value.__get__(self, type(self))
        else:
            return value

    def __setattr__(self, name, value):
        try:
            curvalue = super().__getattribute__(name)
        except AttributeError:
            return super().__setattr__(name, value)

        if hasattr(type(curvalue), '__set__'):
            curvalue.__set__(self, value)
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        value = super().__getattribute__(name)
        if hasattr(type(value), '__delete__'):
            value.__delete__(self)
        else:
            super().__delattr__(name)



class SearchableDict(OrderedDict):
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            for k, v in self.items():
                if k.startswith(key):
                    return v
            raise KeyError
    def search(self, key):
        return SearchableDict((k,v) for k, v in self.items()
                              if k.startswith(key))



class Attr:
    def __init__(self, name, field=None, readonly=False, deletable=False):
        self.name = name
        self.field = field or '_' + name
        self.readonly = readonly
        self.deletable = deletable
    def __get__(self, obj, typ):
        if obj is None:
            return self
        try:
            return vars(obj)[self.field]
        except KeyError:
            raise AttributeError("'{}' is unset".format(self.name)) from None
    def __set__(self, obj, val):
        if self.readonly:
            raise AttributeError("can't set '{}'".format(self.name))
        vars(obj)[self.field] = val
    def __delete__(self, obj):
        if not self.deletable:
            raise AttributeError("can't delete '{}'".format(self.name))
        try:
            del vars(obj)[self.field]
        except KeyError:
            raise AttributeError("'{}' is unset".format(self.name)) from None


class TypedAttr(Attr):
    def __init__(self, name, typ, field=None, deletable=False):
        super().__init__(name, field, deletable=deletable)
        self.typ = typ
    def __set__(self, obj, val):
        if not isinstance(val, self.typ):
            raise TypeError("'{}' must be of type {}".format(
                            self.name, self.typ.__name__))
        super().__set__(obj, val)



class TypedDict(dict):
    def __init__(self, *args, **kwargs):
        self._types = dict(*args, **kwargs)
    def __setitem__(self, key, value):
        if key in self._types:
            typ = self._types[key]
            if not isinstance(value, typ):
                raise TypeError("'{}' must be of type '{}'"
                                .format(key, typ.__name__))
        super().__setitem__(key, value)



class TypedAttrs:
    def __setattr__(self, name, value):
        if name in self._types:
            typ = self._types[name]
            if not isinstance(value, typ):
                raise TypeError("'{}' must be of type '{}'"
                                .format(name, typ.__name__))
        super().__setattr__(name, value)



class MultiSet:
    def __init__(self, *containers):
        self.containers = list(containers)
    def __iter__(self):
        for cont in self.containers:
            yield from cont
    def __contains__(self, value):
        return any(value in cont for cont in self.containers)
    def __len__(self):
        return sum(map(len, self.containers))
    def __repr__(self):
        return '{}({})'.format(type(self).__name__, ', '.join(
            map(repr, self.containers)))


class MultiSeq(MultiSet, cabc.Sequence):
    def __getitem__(self, index):
        if index < 0:
            index += len(self)
        for seq in self.containers:
            if index < len(seq):
                return seq[index]
            index -= len(seq)
        raise IndexError


class MultiList(MultiSeq, cabc.MutableSequence):
    def __setitem__(self, index, value):
        if index < 0:
            index += len(self)
        for seq in self.containers:
            if index < len(seq):
                seq[index] = value
                return
            index -= len(seq)
        raise IndexError
    def __delitem__(self, index):
        if index < 0:
            index += len(self)
        for seq in self.containers:
            if index < len(seq):
                del seq[index]
                return
            index -= len(seq)
        raise IndexError
    def insert(self, index, value):
        l = len(self)
        if index >= l:
            self.append(value)
            return
        if index < 0:
            index += l
        for seq in self.containers:
            if index <= len(seq):
                seq.insert(index, value)
                return
            index -= len(seq)
    def append(self, value):
        self.containers[-1].append(value)



class Tree:
    def __init__(self, *children):
        self.parent = None
        self.children = list(children)
        for child in children:
            if isinstance(child, Tree):
                child.parent = self

    @classmethod
    def from_list(cls, lst, types=(list, tuple)):
        return cls(
            *(cls.from_list(n, types) if isinstance(n, types) else n
              for n in lst))

    @classmethod
    def from_list2(cls, lst, types=(list, tuple)):
        return cls(None,
            *(cls.from_list2(n, types) if isinstance(n, types) else cls(n)
              for n in lst))

    def add(self, *children):
        self.children.extend(children)
        for child in children:
            if isinstance(child, Tree):
                child.parent = self
    def remove(self, *children):
        for child in children:
            self.children.remove(child)
            if isinstance(child, Tree):
                child.parent = None
    @property
    def root(self):
        if self.parent is None:
            return self
        return self.parent.root
    def parents(self):
        if self.parent is not None:
            yield self.parent
            yield from self.parent.parents()
    def descendents(self):
        for child in self:
            yield child
            if isinstance(child, Tree):
                yield from child.descendents()
    def size(self):
        return sum(node.size() for node in self) + 1
    def height(self):
        return max((node.height() for node in self), default=0) + 1
    def __getitem__(self, index):
        return self.children[index]
    def __setitem__(self, index, value):
        self.children[index] = value
    def __delitem__(self, index):
        del self.children[index]
    def __contains__(self, child):
        return child in self.children
    def __iter__(self):
        yield from self.children
    def __len__(self):
        return len(self.children)
    def __eq__(self, other):
        if isinstance(other, Tree):
            return self.children == other.children
        return NotImplemented
    def __repr__(self):
        return '{}({})'.format(type(self).__name__,
                ', '.join(map(repr, self.children)))
    def __str__(self):
        if any(isinstance(c, Tree) for c in self):
            return '{}(\n{}\n)'.format(type(self).__name__,
                textwrap.indent(',\n'.join(map(str, self.children)), ' '*4))
        return repr(self)

##    def print_tree(self, prefix='', last=True):
##        print(prefix + r'\---')
##        prefix += '    ' if last else '|   '
##        for i, node in enumerate(self.children):
##            if isinstance(node, Tree):
##                node.print_tree(prefix, i == len(self)-1)
##            else:
##                print(prefix + str(node))

    def print_tree(self, prefix='', last=True):
        if len(self) and not isinstance(self.children[0], Tree):
            print(prefix + r'\---' + str(self.children[0]))
        else:
            print(prefix + r'\---')
        prefix += '    ' if last else '|   '
        for i, node in enumerate(self.children):
            if isinstance(node, Tree):
                node.print_tree(prefix, i == len(self)-1)
            elif i > 0:
                print(prefix + str(node))



class DataTree(Tree):
    def __init__(self, data, *children):
        self.data = data
        super().__init__(*children)

    def find(self, data):
        if self.data == data:
            return self
        for child in self.children:
            node = child.find(data)
            if node is not None:
                return node
        return None

    def __eq__(self, other):
        if isinstance(other, DataTree):
            return self.data == other.data and self.children == other.children
        return NotImplemented

    def __repr__(self):
        return '{}({})'.format(type(self).__name__,
                ', '.join(map(repr, [self.data] + self.children)))

    def __str__(self):
        if any(isinstance(c, DataTree) for c in self):
            return '{}({},\n{}\n)'.format(type(self).__name__, self.data,
                textwrap.indent(',\n'.join(map(str, self.children)), ' '*4))
        return repr(self)

    def print_tree(self, prefix='', last=True):
        print(prefix + r'\---' + str(self.data))
        prefix += '    ' if last else '|   '
        for i, node in enumerate(self.children):
            if isinstance(node, Tree):
                node.print_tree(prefix, i == len(self)-1)
            else:
                print(prefix + '|---' + str(node))



class BinTree:
    def __init__(self, data=None, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right

    @classmethod
    def from_data(cls, data):
        data = list(data)
        tree = cls(data[0])
        for d in data[1:]:
            tree.insert(d)
        return tree

    @classmethod
    def from_list(cls, lst, types=(list, tuple)):
        return cls(*(cls.from_list(n, types) if isinstance(n, types) else n
                     for n in lst))

    @classmethod
    def from_list2(cls, lst, types=(list, tuple)):
        return cls(None,
            *(cls.from_list2(n, types) if isinstance(n, types) else cls(n)
              for n in lst))

    @classmethod
    def parse(cls, inpt, typ=str):
        if not isinstance(inpt, Scanner):
            inpt = Scanner(inpt)

        if inpt.next_char('[-') == '-':
            return None
        data = typ(inpt.next_token())
        node = cls(data, cls.parse(inpt, typ), cls.parse(inpt, typ))
        inpt.next_char(']')
        return node

    @classmethod
    def from_heap(cls, heap, i=0):
        if i >= len(heap):
            return None
        return cls(heap[i], cls.from_heap(heap, 2*i+1), cls.from_heap(heap, 2*i+2))

    def __iter__(self):
        yield self.left
        yield self.right

    def size(self):
        lefts = self.left.size() if self.left else 0
        rights = self.right.size() if self.right else 0
        return lefts + rights + 1

    def height(self):
        lefth = self.left.height() if self.left else 0
        righth = self.right.height() if self.right else 0
        return max(lefth, righth) + 1

    def descendents(self):
        if self.left:
            yield self.left
            yield from self.left.descendents()
        if self.right:
            yield self.right
            yield from self.right.descendents()

    def preorder(self):
        yield self
        if self.left:
            yield from self.left.preorder()
        if self.right:
            yield from self.right.preorder()

    def inorder(self):
        if self.left:
            yield from self.left.inorder()
        yield self
        if self.right:
            yield from self.right.inorder()

    def postorder(self):
        if self.left:
            yield from self.left.postorder()
        if self.right:
            yield from self.right.postorder()
        yield self

    def preorder_data(self):
        return [n.data for n in self.preorder()]
    def inorder_data(self):
        return [n.data for n in self.inorder()]
    def postorder_data(self):
        return [n.data for n in self.postorder()]

    def descendent_data(self):
        return [n.data for n in self.descendents()]

    def find(self, data):
        if data == self.data:
            return self
        elif data < self.data:
            child = self.left
        else:
            child = self.right
        return child.find(data) if child else None

    def insert(self, data):
        if data < self.data:
            if self.left:
                self.left.insert(data)
            else:
                self.left = type(self)(data)
        else:
            if self.right:
                self.right.insert(data)
            else:
                self.right = type(self)(data)

    def __eq__(self, other):
        if isinstance(other, BinTree):
            return (self.data == other.data and
                    self.left == other.left and self.right == other.right)
        return NotImplemented

    def __repr__(self):
        if self.left or self.right:
            return '{}({!r}, {!r}, {!r})'.format(type(self).__name__,
                    self.data, self.left, self.right)
        return '{}({})'.format(type(self).__name__, self.data)

    def __str__(self):
        if self.left or self.right:
            return '{}({},\n{},\n{}\n)'.format(type(self).__name__,
                    self.data,
                    textwrap.indent(str(self.left), ' '*4),
                    textwrap.indent(str(self.right), ' '*4))
        return repr(self)

    def simple_print(self, indent=0):
        if self.left:
            self.left.simple_print(indent + 1)
        print('\t' * indent + str(self.data))
        if self.right:
            self.right.simple_print(indent + 1)

    def print_tree(self, side='', prefix=''):
        lprefix = prefix + ('|   ' if side == 'r' else '    ')
        if self.left:
            self.left.print_tree('l', lprefix)

        vertex = '/' if side == 'l' else '\\' if side == 'r' else '|'
        data = str(self.data) if self.data is not None else '|'
        print(prefix + vertex + '---' + data)

        rprefix = prefix + ('|   ' if side == 'l' else '    ')
        if self.right:
            self.right.print_tree('r', rprefix)


def heap2tree(heap):
    return BinTree.from_heap(heap)



class Scanner:
    def __init__(self, source):
        if isinstance(source, str):
            source = io.StringIO(source)
        self.file = source

    def next_char(self, allowed=None):
        c = self.file.read(1)
        while c.isspace():
            c = self.file.read(1)
        if not c:
            raise EOFError('end of input')
        if allowed and c not in allowed:
            raise ValueError(' or '.join(map(repr, allowed)) + ' expected')
        return c

    def next_token(self):
        s = ''
        c = self.next_char()
        quote, escape = False, False
        while c and (quote or escape or not c.isspace()):
            if escape:
                s += c
                escape = False
            else:
                if c == '"':
                    quote = not quote
                elif c == '\\':
                    escape = True
                else:
                    s += c
            c = self.file.read(1)
        return s



class COutStream:
    def __init__(self, file=sys.stdout):
        if isinstance(file, str):
            file = open(file)
        self.file = file

    def __lshift__(self, obj):
        print(obj, file=self.file, end='')
        return self

class CInStream:
    def __init__(self, file=sys.stdin):
        if isinstance(file, str):
            file = open(file)
        self.scan = Scanner(file)
        self._eof = False

    def __bool__(self):
        return not self._eof

    def __rshift__(self, name):
        try:
            sys._getframe(1).f_locals[name] = self.scan.next_token()
        except EOFError:
            self._eof = True
        return self




class ModInt(int):
    def __new__(cls, val, mod):
        self = super().__new__(cls, val % mod)
        self.mod = mod
        return self

    template = '''\
def __{0}__(self, other):
    return type(self)(super(ModInt, self).__{0}__(other), self.mod)
'''
    for op in 'add sub mul floordiv mod pow'.split():
        exec(template.format(op))
        exec(template.format('r' + op))

    template = '''\
def __{0}__(self):
    return type(self)(super(ModInt, self).__{0}__(), self.mod)
'''
    for op in 'pos neg'.split():
        exec(template.format(op))

    del template, op

##    def template(op):
##        def f(self, other):
##            return type(self)(getattr(super(), op)(other), self.mod)
##        f.__name__ = op
##        f.__qualname__ = 'ModInt.' + op
##        return f
##
##    for op in 'add sub mul floordiv mod pow'.split():
##        rop = '__r' + op + '__'
##        op = '__' + op + '__'
##        locals()[op] = template(op)
##        locals()[rop] = template(rop)




class IdWrapper:
    def __init__(self, obj):
        if isinstance(obj, IdWrapper):
            self._obj = obj._obj
        else:
            self._obj = obj
    def __eq__(self, other):
        return isinstance(other, IdWrapper) and self._obj is other._obj
    def __hash__(self):
        return object.__hash__(self._obj)
    def __repr__(self):
        return repr(self._obj)


class IdDict(cabc.MutableMapping):
    def __init__(self, *args, **kwargs):
        self._dict = {}
        self.update(*args, **kwargs)
    def __setitem__(self, key, value):
        self._dict[IdWrapper(key)] = value
    def __getitem__(self, key):
        return self._dict[IdWrapper(key)]
    def __delitem__(self, key):
        del self._dict[IdWrapper(key)]
    def __len__(self):
        return len(self._dict)
    def __iter__(self):
        return (k._obj for k in self._dict)
    def __repr__(self):
        return repr(self._dict)
    def copy(self):
        return IdDict(self)


class IdSet(cabc.MutableSet):
    def __init__(self, it=()):
        self._set = set()
        self |= it
    def add(self, obj):
        self._set.add(IdWrapper(obj))
    def discard(self, obj):
        self._set.discard(IdWrapper(obj))
    def __contains__(self, obj):
        return IdWrapper(obj) in self._set
    def __len__(self):
        return len(self._set)
    def __iter__(self):
        return (o._obj for o in self._set)
    def __repr__(self):
        return repr(self._set)
    def copy(self):
        return IdSet(self)
    union = cabc.Set.__or__
    update = cabc.MutableSet.__ior__
    intersection = cabc.Set.__and__
    intersection_update = cabc.MutableSet.__iand__
    difference = cabc.Set.__sub__
    difference_update = cabc.MutableSet.__isub__
    symmetric_difference = cabc.Set.__xor__
    symmetric_difference_update = cabc.MutableSet.__ixor__
    issubset = cabc.Set.__le__
    issuperset = cabc.Set.__ge__



def struct(name, fields, defaults=()):
    """A mutable equivalent of namedtuple"""
    templ = '''\
from collections import OrderedDict

class {name}:
    __slots__ = _fields = {fields}

    def __init__(self, {args}):
        {init}

    def __getitem__(self, index):
        return getattr(self, self._fields[index])

    def __setitem__(self, index, value):
        setattr(self, self._fields[index], value)

    def __delitem__(self, index):
        raise TypeError("struct fields cannot be deleted")

    def __delattr__(self, index):
        raise AttributeError("struct fields cannot be deleted")

    def __iter__(self):
        for f in self._fields:
            yield getattr(self, f)

    def __eq__(self, other):
        return isinstance(other, {name}) and \
               all(a==b for a, b in zip(self, other))

    @property
    def __dict__(self):
        return OrderedDict((f, getattr(self, f))
                           for f in self._fields)

    def __repr__(self):
        return "{name}({fmt})".format(*self)
'''

    if isinstance(fields, str):
        fields = fields.replace(',', ' ').split()
    fields = tuple(fields)

    init = '\n        '.join(map('self.{0} = {0}'.format, fields))
    fmt = ', '.join(map('{}={{!r}}'.format, fields))

    body = templ.format(name=name, fields=repr(fields),
                        args=', '.join(fields), init=init, fmt=fmt)

    ns = {}
    exec(body, ns)
    cls = ns[name]
    cls.__init__.__defaults__ = defaults
    cls._source = body

    return cls



class BiDirIter:
    def __init__(self, seq, ind=-1, forward=True):
        self._seq = seq
        self._i = min(max(ind, -1), len(self._seq))
        self.forward = forward
    @property
    def ind(self):
        return self._i
    @ind.setter
    def ind(self, ind):
        self._i = min(max(ind, -1), len(self._seq))
    def reverse(self):
        self.forward = not self.forward
    def next(self, default=_empty):
        self._i += 1
        if self._i >= len(self._seq):
            self._i = len(self._seq)
            if default != _empty:
                return default
            raise StopIteration
        return self._seq[self._i]
    def prev(self, default=_empty):
        self._i -= 1
        if self._i < 0:
            self._i = -1
            if default != _empty:
                return default
            raise StopIteration
        return self._seq[self._i]
    def jump(self, ind, default=_empty):
        self._i = min(max(ind, -1), len(self._seq))
        return self.curr(default)
    def advance(self, amount, default=_empty):
        return self.jump(self._i + amount, default)
    def curr(self, default=_empty):
        if self._i < 0 or self._i >= len(self._seq):
            if default != _empty:
                return default
            raise IndexError
        return self._seq[self._i]
    def __next__(self):
        if self.forward:
            return self.next()
        else:
            return self.prev()
    def __iter__(self):
        return self



class IterPlus:
    '''List iterator with insert, set and delete functionality.'''
    def __init__(self, lst):
        self._lst = lst
        self._i = -1

    def __next__(self):
        self._i += 1
        try:
            return self._lst[self._i]
        except IndexError:
            self._i = len(self._lst)
            raise StopIteration

    def insert(self, obj):
        self._i += 1
        self._lst.insert(self._i, obj)

    def set(self, obj):
        if self._i < 0:
            raise IndexError
        self._lst[self._i] = obj

    def remove(self):
        if self._i < 0:
            raise IndexError
        del self._lst[self._i]
        self._i -= 1

    def __iter__(self):
        return self


class BiDirIterPlus(BiDirIter, IterPlus):
    pass



class NumberLine:
    def __init__(self, low=-10, high=10, pts=None):
        self.low = low
        self.high = high
        self.array = [False] * (high - low + 1)
        if pts and isinstance(pts[0], bool):
            self.array[:len(pts)] = pts[:high - low + 1]
        else:
            for x in pts:
                self[x] = True
    def __getitem__(self, i):
        if self.low <= i <= self.high:
            return self.array[i - self.low]
        raise IndexError
    def __setitem__(self, i, v):
        if self.low <= i <= self.high:
            self.array[i - self.low] = bool(v)
        else:
            raise IndexError
    def __delitem__(self, i):
        raise TypeError("can't delete items")
    def __iter__(self):
        return iter(self.array)
    def enum(self):
        return enumerate(self, self.low)
##    def __repr__(self):
##        return "NumberLine(%r, %r, %r)" % (self.low, self.high, self.array)
    def __repr__(self):
        return (''.join('%3d' % i for i in range(self.low, self.high+1)) +
                '\n  ' + '--'.join('X' if x else '+' for x in self))
    def __len__(self):
        return self.high - self.low + 1



class Symbol:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)

    unop = '''\
def __{name}__(self):
    return Symbol('%s%r' % ('{op}', self))
'''
    binop = '''\
def __{name}__(self, other):
    return Symbol('(%r %s %r)' % (self, '{op}', other))
def __r{name}__(self, other):
    return Symbol('(%r %s %r)' % (other, '{op}', self))
'''
    for name, op in dict(pos='+', neg='-', invert='~').items():
        exec(unop.format(name=name, op=op))
    for name, op in dict(add='+', sub='-', mul='*', truediv='/', floordiv='//',
                         mod='%', pow='**', and_='&', or_='|', xor='^',
                         lshift='<<', rshift='>>').items():
        exec(binop.format(name=name.rstrip('_'), op=op))
    def __call__(self, *args):
        return Symbol('%r(%s)' % (self, ', '.join(map(repr, args))))



### Proxy: expr | proxy().a[3].b(x).c.d()



class BitFlag(enum.IntEnum):
    def __or__(self, other):
        val = super().__or__(other)
        return type(self)(val) if val is not NotImplemented else val
    def __ror__(self, other):
        val = super().__ror__(other)
        return type(self)(val) if val is not NotImplemented else val

    def __and__(self, other):
        val = super().__and__(other)
        return type(self)(val) if val is not NotImplemented else val
    def __rand__(self, other):
        val = super().__rand__(other)
        return type(self)(val) if val is not NotImplemented else val

    def __xor__(self, other):
        val = super().__xor__(other)
        return type(self)(val) if val is not NotImplemented else val
    def __rxor__(self, other):
        val = super().__rxor__(other)
        return type(self)(val) if val is not NotImplemented else val

    def __invert__(self):
        return type(self)(super().__invert__() & max(type(self)))

class Color(BitFlag):
    black = 0
    red = 1 << 0
    green = 1 << 1
    blue = 1 << 2
    yellow = red | green
    magenta = red | blue
    cyan = green | blue
    white = red | blue | green



class MultiArray(cabc.Sequence):
    def __init__(self, it=None):
        self.lastsize = 0
        self.lists = [[None]]
        if it:
            self.extend(it)
    def append(self, val):
        n = len(self.lists[-1])
        if self.lastsize == n:
            self.lists.append([None]*n*2)
            self.lastsize = 0
        self.lists[-1][self.lastsize] = val
        self.lastsize += 1
    def extend(self, values):
        for v in values:
            self.append(v)
    def _getinds(self, i):
        li = (i + 1).bit_length() - 1
        ii = i - (1 << li) + 1
        if li == len(self.lists) - 1 and ii >= self.lastsize:
            raise IndexError
        return li, ii
    def __getitem__(self, i):
        li, ii = self._getinds(i)
        return self.lists[li][ii]
    def __setitem__(self, i, value):
        li, ii = self._getinds(i)
        self.lists[li][ii] = value
    def __len__(self):
        return len(self.lists[-1]) - 1 + self.lastsize
    def __repr__(self):
        return 'MultiArray({})'.format(list(self))



class CircleArray(cabc.Sequence):
    def __init__(self, it=None):
        self.arr = [None]
        self.begin = self.end = 0
        self.full = False
        if it:
            self.extend(it)
    def resize(self):
        n = len(self.arr)
        self.arr *= 2
        self.arr[n : n + self.end] = self.arr[:self.end]
        self.end += n
    def append(self, val):
        if self.full:
            self.resize()
        self.arr[self.end] = val
        self.end = (self.end + 1) % len(self.arr)
        self.full = self.begin == self.end
    def appendleft(self, val):
        if self.full:
            self.resize()
        self.begin = (self.begin - 1) % len(self.arr)
        self.arr[self.begin] = val
        self.full = self.begin == self.end
    def extend(self, values):
        for v in values:
            self.append(v)
    def extendleft(self, values):
        for v in values:
            self.appendleft(v)
    def pop(self):
        if len(self) == 0:
            raise IndexError
        self.end = (self.end - 1) % len(self.arr)
        val = self.arr[self.end]
        self.full = False
        return val
    def popleft(self):
        if len(self) == 0:
            raise IndexError
        val = self.arr[self.begin]
        self.begin = (self.begin + 1) % len(self.arr)
        self.full = False
        return val
    def __getitem__(self, ind):
        n = len(self)
        if not -n <= ind < n:
            raise IndexError
        return self.arr[(self.begin + ind) % len(self.arr)]
    def __setitem__(self, ind, val):
        n = len(self)
        if not -n <= ind < n:
            raise IndexError
        self.arr[(self.begin + ind) % len(self.arr)] = val
    def __len__(self):
        n = self.end - self.begin
        if n < 0 or self.full:
            n += len(self.arr)
        return n
    def __repr__(self):
        return 'CircleArray({})'.format(list(self))


class PrettyODict(OrderedDict):
    @reprlib.recursive_repr()
    def __repr__(self):
        return '{' + ', '.join('%r: %r' % (k, v) for k, v in self.items()) + '}'

class ReprStr(str):
    def __repr__(self):
        return str(self)

class _BaseInt(int):
    def __new__(cls, x, width, base):
        if isinstance(x, str):
            self = super().__new__(cls, x, base)
        else:
            self = super().__new__(cls, x)
        self.width = width
        return self
    @classmethod
    def w(cls, width):
        return functools.partial(cls, width=width)

class BinInt(_BaseInt):
    def __new__(cls, x=0, width=0, base=2):
        return super().__new__(cls, x, width, base)
    def __repr__(self):
        return '{:#0{}b}'.format(self, self.width + 2)

class HexInt(_BaseInt):
    def __new__(cls, x=0, width=0, base=16):
        return super().__new__(cls, x, width, base)
    def __repr__(self):
        return '{:#0{}x}'.format(self, self.width + 2)

class OctInt(_BaseInt):
    def __new__(cls, x=0, width=0, base=8):
        return super().__new__(cls, x, width, base)
    def __repr__(self):
        return '{:#0{}o}'.format(self, self.width + 2)



class OrderedSet(cabc.MutableSet):
    def __init__(self, iterable=()):
        self._odict = OrderedDict.fromkeys(iterable)
    def __len__(self):
        return len(self._odict)
    def __iter__(self):
        return iter(self._odict)
    def __reversed__(self):
        return reversed(self._odict)
    def __contains__(self, value):
        return value in self._odict
    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return self._odict == other._odict
        return self._odict.keys() == other
    def __repr__(self):
        return '{}({})'.format(type(self).__name__, list(self))
    def add(self, value):
        self._odict[value] = None
    def discard(self, value):
        self._odict.pop(value, None)
    def remove(self, value):
        del self._odict[value]
    def pop(self, last=True):
        return self._odict.popitem(last)[0]
    def clear(self):
        self._odict.clear()
    def copy(self):
        return OrderedSet(self._odict)
    def move_to_end(self, value, last=True):
        self._odict.move_to_end(value, last)
    def union(self, other):
        return self | other
    def update(self, other):
        self |= other
    def intersection(self, other):
        return self & other
    def intersection_update(self, other):
        self &= other
    def difference(self, other):
        return self - other
    def difference_update(self, other):
        self -= other
    def symmetric_difference(self, other):
        return self ^ other
    def symmetric_difference_update(self, other):
        self ^= other
    def issubset(self, other):
        return self <= other
    def issuperset(self, other):
        return self >= other



class DefValDict(dict):
    def __init__(self, _defval=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._defval = _defval
    def __missing__(self, key):
        return self._defval



class NamedProp(property):
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super().__init__(fget, fset, fdel, doc)
        self.__name__ = self.__qualname__ = None
    def __set_name__(self, owner, name):
        self.__name__ = name
        self.__qualname__ = owner.__qualname__ + '.' + name
        self.__objclass__ = owner
    def __repr__(self):
        bits = 32 if sys.maxsize <= 2**31 - 1 else 64
        return '<property {} at 0x{:0{}X}>'.format(
            self.__qualname__ or 'object', id(self), bits//4)



class view:
    def __init__(self, seq, start=None, stop=None, step=1):
        self.seq = seq
        if isinstance(start, slice):
            slc = start
        else:
            slc = slice(start, stop, step)
        self.start, self.stop, self.step = slc.indices(len(seq))
        self.len = max(0, -(-(self.stop - self.start) // self.step))
    def __len__(self):
        return self.len
    def __iter__(self):
        seq = self.seq
        for i in range(self.start, self.stop, self.step):
            yield seq[i]
    def _get_slice(self, slc):
        istart, istop, istep = slc.indices(self.len)
        start = self.start + self.step*istart
        stop = self.start + self.step*istop
        return slice(start if start >= 0 else start - len(self.seq),
                     stop if stop >= 0 else stop - len(self.seq),
                     self.step*istep)
    def _get_ind(self, i):
        if i < 0:
            i += self.len
        if not 0 <= i < self.len:
            raise IndexError
        return self.start + self.step*i
    def __getitem__(self, i):
        if isinstance(i, slice):
            return view(self.seq, self._get_slice(i))
        return self.seq[self._get_ind(i)]
    def __setitem__(self, i, val):
        if isinstance(i, slice):
            self.seq[self._get_slice(i)] = val
            return
        self.seq[self._get_ind(i)] = val
    def __repr__(self):
        return '<view({})>'.format(list(self))


class DynamicPrompt:
    def __init__(self, func):
        self.func = func
    def __str__(self):
        return self.func()



class MapSeq(cabc.Sequence):
    def __init__(self, seq, func):
        self.seq = seq
        self.func = func

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            return list(map(self.func, self.seq[ind]))
        return self.func(self.seq[ind])

    def __len__(self):
        return len(self.seq)



class Indexer:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        f = fget or fset or fdel
        self.__doc__ = doc or getattr(f, '__doc__', None)
        self.__name__ = getattr(f, '__name__', None)
        self.__qualname__ = getattr(f, '__qualname__', self.__name__)

    def __repr__(self):
        return '<Indexer {} at 0x{:016X}>'.format(self.__qualname__, id(self))

    def __getitem__(self, key):
        if self.fget is None:
            raise TypeError('cannot get item')
        return self.fget(key)

    def __setitem__(self, key, value):
        if self.fset is None:
            raise TypeError('cannot set item')
        self.fset(key, value)

    def __delitem__(self, key):
        if self.fdel is None:
            raise TypeError('cannot delete item')
        self.fdel(key)


class IndexerDescriptor:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        f = fget or fset or fdel
        self.__doc__ = doc or (f and f.__doc__)
        self.__name__ = f and f.__name__
        self.__qualname__ = f and f.__qualname__

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        indexer = Indexer(
            self.fget.__get__(instance, owner),
            self.fset.__get__(instance, owner),
            self.fdel.__get__(instance, owner),
            self.__doc__)
        indexer.__name__ = self.__name__
        indexer.__qualname__ = self.__qualname__
        return indexer

    def getter(self, fget):
        self.fget = fget
        return self

    def setter(self, fset):
        self.fset = fset
        return self

    def deleter(self, fdel):
        self.fdel = fdel
        return self


class StructureRepr(ctypes.Structure):
    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            ', '.join(f'{n}={getattr(self, n)}' for n, t in self._fields_)
        )


def tuple_struct(*types):
    class TupleStruct(ctypes.Structure):
        _fields_ = [(f'_{i}', typ) for i, typ in enumerate(types)]

        def __repr__(self):
            fields = ', '.join(map(repr, self))
            return f'{type(self).__name__}({fields})'

        def __iter__(self):
            for f, t in self._fields_:
                yield getattr(self, f)

        def __getitem__(self, ind):
            if isinstance(ind, slice):
                fields = self._fields_[ind]
                return tuple(getattr(self, f[0]) for f in fields)
            return getattr(self, self._fields_[ind][0])

    TupleStruct.__name__ = 'tuple_' + '__'.join(t.__name__ for t in types)
    TupleStruct.__qualname__ = TupleStruct.__name__
    return TupleStruct


class c_uint80(ctypes.Structure):
    _fields_ = [('data', ctypes.c_uint8*10)]

    def __init__(self, x):
        self.data = (ctypes.c_uint8*10)(*x.to_bytes(10, 'little'))

    def __repr__(self):
        return f'c_uint80({hex(self)})'

    @property
    def value(self):
        return int.from_bytes(self.data, 'little')

    def __index__(self):
        return self.value


class BitField:
    def __init__(self, varname, offset, size):
        self.varname = varname
        self.offset = offset
        self.size = size
        self.mask = ((1 << size) - 1) << offset

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return (getattr(instance, self.varname) & self.mask) >> self.offset

    def __set__(self, instance, value):
        value = (value << self.offset) & self.mask
        varval = getattr(instance, self.varname) & ~self.mask
        setattr(instance, self.varname, varval | value)


class LazyProp:
    def __init__(self, func, field=None):
        self.func = func
        self.field = field

    def __set_name__(self, owner, name):
        self.field = self.field or name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return instance.__dict__[self.field]
        except KeyError:
            val = self.func(instance)
            setattr(instance, self.field, val)
            return val


def with_generator(gen_func):
    class WithGenerator:
        def __init__(self, gen):
            self.gen = gen

        def __iter__(self):
            return self

        def __next__(self):
            return self.gen.__next__()

        def __getattr__(self, attr):
            return getattr(self.gen, attr)

        def close(self):
            self.gen.close()

        def __enter__(self):
            return self.gen

        def __exit__(self, *exc):
            self.close()

    return functools.update_wrapper(
        lambda *args, **kwargs: WithGenerator(gen_func(*args, **kwargs)),
        gen_func)
