def leading_1s(b):
    return 8 - (~b & 0xff).bit_length()
##    i = 0
##    while b & 0x80:
##        b <<= 1
##        i += 1
##    return i

def decode_utf8(bs):
    cs = []
    rem = 0
    c = 0
    for b in bs:
        n = leading_1s(b)
        if n == 0:
            if rem != 0:
                raise UnicodeDecodeError('single-byte char inside multibyte char')
            cs.append(chr(b))
        elif n == 1:
            if rem == 0:
                raise UnicodeDecodeError('continuation byte outside multibyte char')
            c = (c << 6) | (b & 0x3f)
            rem -= 1
            if rem == 0:
                cs.append(chr(c))
        else:
            if rem != 0:
                raise UnicodeDecodeError('multibyte char start inside multibyte char')
            c = b & (0x7f >> n)
            rem = n - 1
    return ''.join(cs)

def encode_utf8(s):
    bs = bytearray()
    for c in s:
        c = ord(c)
        if c < 0x80:
            bs.append(c)
        else:
            b = bytearray()
            n = 1
            # while c.bit_length() > 7-n:
            while c > (0x7f >> n):
                b.append(c & 0x3f | 0x80)
                c >>= 6
                n += 1
            bs.append((-0x100 >> n) & 0xff | c)
            bs.extend(b[::-1])
    return bytes(bs)
