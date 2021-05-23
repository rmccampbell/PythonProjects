from itertools import islice
from math import sqrt, log

__all__ = ['pfactor', 'factor', 'isprime', 'primes', 'nprimes', 'nthprime',
           'pfactori', 'factori', 'primesi', 'nprimesi']

# def pfactori(n):
#     for i in range(2, int(sqrt(abs(n)))+1):
#         q, r = divmod(n, i)
#         if r == 0:
#             yield i
#             for f in pfactori(q):
#                 yield f
#             return
#     if abs(n) > 1:
#         yield n

def pfactori(n):
    n = abs(n)
    if n <= 1:
        return
    while n % 2 == 0:
        yield 2
        n //= 2
    i = 3
    while i*i <= n:
        while n % i == 0:
            yield i
            n //= i
        i += 2
    if n > 1:
        yield n

def factori(n):
    for i in range(1, int(sqrt(abs(n)))+1):
        q, r = divmod(n, i)
        if r == 0:
            yield i, q

def isprime(n):
    if n < 2 or (n > 2 and n % 2 == 0):
        return False
    for i in range(3, int(sqrt(n))+1, 2):
        if n % i == 0:
            return False
    return True

def primesi(n):
    sieve = [True] * n
    for p in range(2, n):
        if sieve[p]:
            yield p
            for i in range(p*p, n, p):
                sieve[i] = False

def nprimesi(n):
    b = int(n * (log(n) + log(log(n)))) if n > 9 else 24
    return islice(primesi(b), n)

def nthprime(n):
    return next(islice(nprimesi(n+1), n, None))

for f in ('pfactor', 'factor', 'primes', 'nprimes'):
    exec('def {0}(n): return list({0}i(n))'.format(f))
del f
