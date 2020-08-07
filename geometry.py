import math

# Invert float or vector; return signed infinity for +-0
def inv(x):
    # Note vectors are never equal to 0
    return 1./x if x != 0. else math.copysign(math.inf, x)


def clamp(x, low, high):
    if isinstance(x, Vec3):
        return x.max(low).min(high)
    return min(max(x, low), high)


def _broadcast(x):
    if hasattr(x, '__iter__'):
        return x
    return x, x, x


class Vec3:
    __slots__ = ('x', 'y', 'z')

    def __init__(self, x=0.0, y=None, z=None, unit=False):
        if y is z is None:
            x, y, z = _broadcast(x)
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        if unit:
            self.normalize()

    def __eq__(self, other):
        return (isinstance(other, Vec3) and
                self.x == other.x and self.y == other.y and self.z == other.z)

    def __bool__(self):
        return self.x or self.y or self.z

    def len(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def len_sq(self):
        return self.x**2 + self.y**2 + self.z**2

    def unit(self):
        return self and self / self.len()

    def normalize(self):
        self /= self.len() or 1

    def dot(self, other):
        x, y, z = other
        return self.x*x + self.y*y + self.z*z

    __matmul__ = __rmatmul__ = dot

    def cross(self, other):
        x, y, z = other
        return Vec3(self.y*z - self.z*y,
                    self.z*x - self.x*z,
                    self.x*y - self.y*x)

    def __pos__(self):
        return Vec3(self.x, self.y, self.z)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __abs__(self):
        return Vec3(abs(self.x), abs(self.y), abs(self.z))

    def __add__(self, other):
        x, y, z = _broadcast(other)
        return Vec3(self.x+x, self.y+y, self.z+z)

    def __sub__(self, other):
        x, y, z = _broadcast(other)
        return Vec3(self.x-x, self.y-y, self.z-z)

    def __mul__(self, other):
        x, y, z = _broadcast(other)
        return Vec3(self.x*x, self.y*y, self.z*z)

    def __rmul__(self, other):
        return Vec3(self.x*other, self.y*other, self.z*other)

    def __truediv__(self, other):
        return self*inv(other)

    def __rtruediv__(self, other):
        return Vec3(other*inv(self.x), other*inv(self.y), other*inv(self.z))

    def __pow__(self, other):
        return Vec3(self.x**other, self.y**other, self.z**other)

    def __iadd__(self, other):
        x, y, z = _broadcast(other)
        self.x += x
        self.y += y
        self.z += z
        return self

    def __isub__(self, other):
        x, y, z = _broadcast(other)
        self.x -= x
        self.y -= y
        self.z -= z
        return self

    def __imul__(self, other):
        x, y, z = _broadcast(other)
        self.x *= x
        self.y *= y
        self.z *= z
        return self

    def __itruediv__(self, other):
        self *= inv(other)
        return self

    def __ipow__(self, other):
        self.x **= other
        self.y **= other
        self.z **= other
        return self

    def __repr__(self):
        return 'Vec3(%r, %r, %r)' % (self.x, self.y, self.z)

    def __len__(self):
        return 3

    def __getitem__(self, index):
        return (self.x, self.y, self.z)[index]

    def __setitem__(self, index, value):
        elts = [self.x, self.y, self.z]
        elts[index] = value
        (self.x, self.y, self.z) = elts

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __getattr__(self, name):
        if set(name) <= {'x', 'y', 'z'}:
            return [getattr(self, c) for c in name]
        return self.__getattribute__(name)

    def __setattr__(self, name, value):
        if len(name) > 1 and set(name) <= {'x', 'y', 'z'}:
            for c, v in zip(name, value):
                setattr(self, c, v)
        else:
            super().__setattr__(name, value)

    def min(self, other):
        x, y, z = _broadcast(other)
        return Vec3(min(self.x, x), min(self.y, y), min(self.z, z))

    def max(self, other):
        x, y, z = _broadcast(other)
        return Vec3(max(self.x, x), max(self.y, y), max(self.z, z))


class Ray:
    def __init__(self, o, d, unit=True):
        self.o = Vec3(o)
        self.d = Vec3(d, unit=unit)

    def __call__(self, t):
        return self.o + self.d*t

    def __repr__(self):
        return 'Ray(%r, %r)' % (self.o, self.d)


class Sphere:
    def __init__(self, c, r):
        self.c = Vec3(c)
        self.r = float(r)

    def __repr__(self):
        return 'Sphere(%r, %r)' % (self.c, self.r)

    def intersect(self, ray):
        oc = self.c - ray.o
        d_oc = ray.d.dot(oc)
        d_d = ray.d.len_sq() # 1 for unit vector
        disc = d_oc**2 - d_d*(oc.len_sq() - self.r**2)
        if disc < 0:
            return -1.
        root = math.sqrt(disc)
        if d_oc - root >= 0:
            return (d_oc - root)/d_d
        if d_oc + root >= 0:
            return (d_oc + root)/d_d
        return -1.


class Plane:
    def __init__(self, n, d, unit=True):
        self.n = Vec3(n, unit=unit)
        self.d = float(d)

    def __repr__(self):
        return 'Plane(%r, %r)' % (self.n, self.d)

    def intersect(self, ray):
        # Avoid divide by zero
        d_n = ray.d.dot(self.n) + 1e-20
        t = (self.d - ray.o.dot(self.n)) / d_n
        return t if t >= 0 else -1.


class Triangle:
    def __init__(self, v1, v2, v3):
        self.v1 = Vec3(v1)
        self.v2 = Vec3(v2)
        self.v3 = Vec3(v3)

    def __repr__(self):
        return 'Triangle(%r, %r, %r)' % (self.v1, self.v2, self.v3)

    def intersect(self, ray):
        # Todo: bary coordinates?
        v1, v2, v3 = self.v1, self.v2, self.v3
        n = (v2 - v1).cross(v3 - v1)
        d_n = ray.d.dot(n) + 1e-20
        ov1, ov2, ov3 = v1 - ray.o, v2 - ray.o, v3 - ray.o
        if (ov1.cross(ov2).dot(ray.d) * d_n < 0. or
            ov2.cross(ov3).dot(ray.d) * d_n < 0. or
            ov3.cross(ov1).dot(ray.d) * d_n < 0.):
            return -1.
        # Plane intersection
        t = n.dot(v1 - ray.o) / d_n
        if t < 0:
            return -1.
        return t


class BBox:
    def __init__(self, p1, p2):
        self.p1 = Vec3(p1)
        self.p2 = Vec3(p2)

    @property
    def size(self):
        return self.p2 - self.p1

    @property
    def center(self):
        return (self.p1 + self.p2) / 2.

    def __repr__(self):
        return 'BBox(%r, %r)' % (self.p1, self.p2)

    def intersect(self, ray):
        # Avoid divide by zero
        dinv = 1 / (ray.d + 1e-20)
        t1 = (self.p1 - ray.o)*dinv
        t2 = (self.p2 - ray.o)*dinv

        tmin = max(t1.min(t2))
        tmax = min(t1.max(t2))

        if tmin > tmax or tmax < 0.: return -1.
        if tmin < 0.: return tmax # or 0
        return tmin
