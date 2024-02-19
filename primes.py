import random
from itertools import islice, repeat
from math import isqrt, log

def pfactor_i(n):
    n = abs(n)
    if n <= 1:
        return
    def _reduce(n, i, c=0):
        while (m := n // i) * i == n:
            c += 1
            n = m
        return n, c
    n, c = _reduce(n, 2)
    if c: yield (2, c)
    n, c = _reduce(n, 3)
    if c: yield (3, c)
    i = 5
    while i*i <= n:
        n, c = _reduce(n, i)
        if c: yield (i, c)
        n, c = _reduce(n, i+2)
        if c: yield (i+2, c)
        i += 6
    if n > 1:
        yield (n, 1)

def xpfactor_i(n):
    for (p, c) in pfactor_i(n):
        yield from repeat(p, c)

def factor_i(n):
    for i in range(1, isqrt(abs(n))+1):
        q, r = divmod(n, i)
        if r == 0:
            yield i, q

def isprime(n):
    if n < 2 or (n > 2 and n % 2 == 0):
        return False
    for i in range(3, isqrt(n)+1, 2):
        if n % i == 0:
            return False
    return True

def primes_i(n):
    sieve = [True] * n
    for p in range(2, n):
        if sieve[p]:
            yield p
            for i in range(p*p, n, p):
                sieve[i] = False

def nprimes_i(n):
    b = int(n * (log(n) + log(log(n)))) if n > 9 else 24
    return islice(primes_i(b), n)

def nthprime(n):
    return next(islice(nprimes_i(n+1), n, None))


def fermat_test(n, k=20):
    for i in range(k):
        a = random.randrange(2, n-1)
        if pow(a, n-1, n) != 1:
            return False
    return True

def miller_rabin_test(n, k=20):
    m = n - 1
    s = (m ^ (m-1)).bit_length() - 1
    d = m >> s
    for i in range(k):
        a = random.randrange(2, m)
        x = pow(a, d, n)
        for j in range(s):
            y = pow(x, 2, n)
            if y == 1 and x != 1 and x != m:
                return False
            x = y
        if x != 1:
            return False
    return True

def rand_prime(bits, k=20):
    while True:
        p = random.getrandbits(bits)
        if miller_rabin_test(p, k):
            return p


for f in ('pfactor', 'xpfactor', 'factor', 'primes', 'nprimes'):
    exec('def {0}(n): return list({0}_i(n))'.format(f))
del f
