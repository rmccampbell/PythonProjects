from itertools import zip_longest

__all__ = ['BigInt']

class BigInt:
    def __new__(cls, value=0):
        if isinstance(value, BigInt):
            return value
        self = super().__new__(cls)
        if value == 0:
            self.data = b''
        elif isinstance(value, int):
            if value < 0x100:
                self.data = _bchr(value)
            else:
                size = (value.bit_length() + 7) // 8
                self.data = bytes([value >> 8*i & 0xff for i in range(size)])
        else:
            self.data = data = bytes(value)
        return self

    def __int__(self):
        return sum(n << 8*i for i, n in enumerate(self.data))

    def __index__(self):
        return int(self)

    def __pos__(self):
        return self

    def __repr__(self):
        if len(self.data) is 0:
            return 'BigInt(0)'
        return 'BigInt(0x%s)' % self.data[::-1].hex()

    def __len__(self):
        return len(self.data)

    def __bool__(self):
        return self.data != b''

    def __eq__(self, other):
        return self.data == BigInt(other).data

    def _cmp(self, other):
        other = BigInt(other)
        m = len(self.data)
        n = len(other.data)
        if m < n:
            return -1
        elif m > n:
            return 1
        for x, y in zip(reversed(self.data), reversed(other.data)):
            if x < y:
                return -1
            elif x > y:
                return 1
        return 0

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __and__(self, other):
        return BigInt([a & b for a, b in zip(
            self.data, BigInt(other).data)])

    def __or__(self, other):
        return BigInt([a | b for a, b in zip_longest(
            self.data, BigInt(other).data, fillvalue=0)])

    def __xor__(self, other):
        return BigInt(_strip([a ^ b for a, b in zip_longest(
            self.data, BigInt(other).data, fillvalue=0)]))

    def __lshift__(self, shift):
        bsh, sh = divmod(shift, 8)
        n = len(self.data)
        if n == 0: return BigInt()
        data = bytearray(n + bsh + 1)
        for i, x in enumerate(self.data):
            data[i + bsh] |= x << sh & 0xff
            data[i + bsh + 1] = x >> (8-sh)
        return BigInt(_strip(data))

    def __rshift__(self, shift):
        bsh, sh = divmod(shift, 8)
        n = len(self.data)
        if bsh >= n: return BigInt()
        data = bytearray(n - bsh)
        data[0] = self.data[bsh] >> sh
        for i in range(bsh + 1, n):
            x = self.data[i]
            data[i - bsh] = x >> sh
            data[i - bsh - 1] |= x << (8-sh) & 0xff
        return BigInt(_strip(data))

    def __add__(self, other):
        other = BigInt(other)
        m, n = len(self.data), len(other.data)
        if not m:
            return other
        if not n:
            return self
        data = bytearray(max(m, n))
        s = 0
        for i, (x, y) in enumerate(
                zip_longest(self.data, other.data, fillvalue=0)):
            s += x + y
            data[i] = s & 0xff
            s >>= 8
        if s:
            data.append(s)
        return BigInt(data)

    def __sub__(self, other):
        other = BigInt(other)
        m, n = len(self.data), len(other.data)
        if not n:
            return self
        data = bytearray(max(m, n))
        d = 0
        for i, (x, y) in enumerate(
                zip_longest(self.data, other.data, fillvalue=0)):
            d += x - y
            data[i] = d & 0xff
            d >>= 8
        return BigInt(_strip(data))

    def __mul__(self, other):
        other = BigInt(other)
        data1, data2 = self.data, other.data
        m, n = len(data1), len(data2)
        if not (m and n):
            return BigInt()
        if m < n:
            data1, data2 = data2, data1
        data = bytearray(m + n)
        for i, x in enumerate(data1):
            s = 0
            for j, y in enumerate(data2):
                s += data[i + j] + x*y
                data[i + j] = s & 0xff
                s >>= 8
            if s:
                data[i + j + 1] = s
        return BigInt(_strip(data))

    def __divmod__(self, other):
        other = BigInt(other)
        n = len(other.data)
        if n == 0:
            raise ZeroDivisionError()
        elif n == 1:
            return self._idivmod(other.data[0])
        return self._divmod(other)

    def _divmod(self, other):
        m, n = len(self.data), len(other.data)
        if m < n or self < other:
            return BigInt(), self
        a, b = self.data[-1], other.data[-1]
        bsh = m - n
        if a < b:
            a = ((a << 8) | self.data[-2])
            bsh -= 1
        q = a // b
        Q = BigInt(b'\0' * bsh + _bchr(q))
        y = BigInt(b'\0' * bsh + (other * q).data)
        cmp = y._cmp(self)
        if cmp == 0:
            return Q, BigInt()
        elif cmp < 0:
            R = self - y
            Q2, R = R._divmod(other)
            return Q + Q2, R
        else:
            R = y - self
            Q2, R = R._divmod(other)
            if R:
                return Q - Q2 - 1, other - R
            return Q - Q2, R

    def _idivmod(self, other):
        data1 = self.data
        Q = bytearray(len(data1))
        r = 0
        for i in reversed(range(len(data1))):
            r = (r << 8) | data1[i]
            q = Q[i] = r // other
            r -= q * other
        return BigInt(_strip(Q)), BigInt(r)

    def __floordiv__(self, other):
        return self.__divmod__(other)[0]

    def __mod__(self, other):
        return self.__divmod__(other)[1]


def _bchr(i):
    return i.to_bytes(1, 'little')

def _strip(data):
    while data and not data[-1]:
        data.pop()
    return data
