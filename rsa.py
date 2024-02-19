import primes, math

# def mod_inv(e, n):
#     r0, r1 = e, n
#     s0, s1 = 1, 0
#     t0, t1 = 0, 1
#     while r1:
#         r0, (q, r1) = r1, divmod(r0, r1)
#         s0, s1 = s1, s0 - q*s1
#         t0, t1 = t1, t0 - q*t1
#     return s0 % n

def mod_inv(e, n):
    return pow(e, -1, n)

def gen_key(bits=128, iters=20):
    p = primes.rand_prime(bits, iters)
    q = primes.rand_prime(bits, iters)
    n = p*q
    l = math.lcm(p-1, q-1)
    e = 65537
    d = mod_inv(e, l)
    return (n, e), (n, e, d)

def encrypt(m, pubk):
    n, e = pubk
    if isinstance(m, bytes):
        m = int.from_bytes(m, 'little')
    c = pow(m, e, n)
    return c.to_bytes((c.bit_length() + 7) // 8, 'little')

def decrypt(c, privk):
    n, e, d = privk
    if isinstance(c, bytes):
        c = int.from_bytes(c, 'little')
    m = pow(c, d, n)
    return m.to_bytes((m.bit_length() + 7) // 8, 'little')
