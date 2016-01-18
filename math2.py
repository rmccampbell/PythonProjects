from itertools import islice
from math import sqrt, log

__all__ = ['pfactor', 'factor', 'is_prime', 'primes', 'n_primes',
           'pfactorl', 'factorl', 'primesl', 'n_primesl']

def pfactor(x):
    for i in range(2, int(sqrt(abs(x)))+1):
        q, r = divmod(x, i)
        if r == 0:
            yield i
            for f in pfactor(q):
                yield f
            return
    if abs(x) > 1:
        yield x

def factor(x):
    for i in range(1, int(sqrt(abs(x)))+1):
        q, r = divmod(x, i)
        if r == 0:
            yield i, q

def is_prime(n):
    rt = sqrt(abs(n))
    if rt.is_integer():
        return False
    for i in range(2, int(rt)+1):
        if n % i == 0:
            return False
    return True

def primes(n):
    sieve = [False] * n
    for p in range(2, n):
        if sieve[p]: continue
        yield p
        for i in range(p**2, n, p):
            sieve[i] = True

def n_primes(n):
    b = n * int(log(n) + log(log(n))) if n > 9 else 24
    return islice(primes(b), n)


def pfactorl(x):
    return list(pfactor(x))

def factorl(x):
    return list(factor(x))

def primesl(x):
    return list(primes(x))

def n_primesl(x):
    return list(n_primes(x))

