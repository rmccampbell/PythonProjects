from itertools import islice
from math import sqrt, log

__all__ = ['pfactor', 'factor', 'isprime', 'primes', 'nprimes', 'nthprime',
           'lpfactor', 'lfactor', 'lprimes', 'lnprimes']

def pfactor(n):
    for i in range(2, int(sqrt(abs(n)))+1):
        q, r = divmod(n, i)
        if r == 0:
            yield i
            for f in pfactor(q):
                yield f
            return
    if abs(n) > 1:
        yield n

def factor(n):
    for i in range(1, int(sqrt(abs(n)))+1):
        q, r = divmod(n, i)
        if r == 0:
            yield i, q

def isprime(n):
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

def nprimes(n):
    b = int(n * (log(n) + log(log(n)))) if n > 9 else 24
    return islice(primes(b), n)

def nthprime(n):
    return next(islice(nprimes(n+1), n, None))

for f in ('pfactor', 'factor', 'primes', 'nprimes'):
    exec('def l{0}(n): return list({0}(n))'.format(f))
del f
