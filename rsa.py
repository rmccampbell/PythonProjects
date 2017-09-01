def mod_inv(e, n):
    r0, r1 = e, n
    s0, s1 = 1, 0
    t0, t1 = 0, 1
    while r1:
        r0, (q, r1) = r1, divmod(r0, r1)
        s0, s1 = s1, s0 - q*s1
        t0, t1 = t1, t0 - q*t1
    return s0

def encrypt(s, e, n):
    return [pow(c, e, n) for c in s]

def decrypt(s, d, n):
    return bytes(pow(c, d, n) for c in s)
