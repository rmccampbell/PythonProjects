import numpy as np
from numpy.linalg import inv, norm, matrix_power as powm
from numpy import pi

deg = pi / 180

I2 = np.eye(2)
I3 = np.eye(3)
I4 = np.eye(4)


def vec(a, n=4, homo=None):
    if homo is None: homo = n == 4
    a = np.asarray(a, float)
    if a.ndim != 1: a = a.ravel()
    if a.size < n:
        b = np.zeros(n)
        if homo:
            b[-1] = 1
        b[:a.size] = a
        return b
    elif a.size > n:
        return a[:n]
    return a

def vec2(x, y=None):
    if y is None:
        return vec(x, 2, False)
    return np.array([x, y], float)

def vec3(x, y=None, z=0, homo=False):
    if y is None:
        return vec(x, 3, homo)
    return np.array([x, y, z], float)

def vec4(x, y=None, z=0, w=1):
    if y is None:
        return vec(x, 4, True)
    return np.array([x, y, z, w], float)

def normalize(v):
    return v / norm(v)

def unit2(x, y=None):
    v = vec2(x, y)
    return v / norm(v)

def unit3(x, y=None, z=0, homo=False):
    if homo:
        return vec(unit2(x, y), 3, True)
    v = vec3(x, y, z)
    return v / norm(v)

def unit4(x, y=None, z=0):
    return vec(unit3(x, y, z), 4, True)

def mat(arr, n):
    arr = np.atleast_2d(arr)
    arr2 = np.eye(n)
    h, w = arr.shape
    arr2[:h, :w] = arr[:n, :n]
    return arr2

def mat2(arr):
    return mat(arr, 2)

def mat3(arr):
    return mat(arr, 3)

def mat4(arr):
    return mat(arr, 4)

def ident2():
    return np.eye(2)

def ident3():
    return np.eye(3)

def ident4():
    return np.eye(4)


def scale2(x, y=None):
    if y is None: y = x
    return np.diag([x, y])

def scale3(x, y=None, z=None):
    if y is None: y = z = x
    elif z is None: z = 1
    return np.diag([x, y, z])

def scale4(x, y=None, z=None):
    if y is None: y = z = x
    elif z is None: z = 1
    return np.diag([x, y, z, 1])

def rot2(th):
    return np.array([[np.cos(th), -np.sin(th)],
                     [np.sin(th),  np.cos(th)]])

def rotx3(th):
    return np.array([[1, 0,           0,        ],
                     [0, np.cos(th), -np.sin(th)],
                     [0, np.sin(th),  np.cos(th)]])

def roty3(th):
    return np.array([[ np.cos(th), 0, np.sin(th)],
                     [ 0,          1, 0         ],
                     [-np.sin(th), 0, np.cos(th)]])

def rotz3(th):
    return np.array([[np.cos(th), -np.sin(th), 0],
                     [np.sin(th),  np.cos(th), 0],
                     [0,           0,          1]])

rot3 = rotz3

def rotx4(th):
    return np.array([[1, 0,           0,          0],
                     [0, np.cos(th), -np.sin(th), 0],
                     [0, np.sin(th),  np.cos(th), 0],
                     [0, 0,           0,          1]])

def roty4(th):
    return np.array([[ np.cos(th), 0, np.sin(th), 0],
                     [ 0,          1, 0,          0],
                     [-np.sin(th), 0, np.cos(th), 0],
                     [ 0,          0, 0,          1]])

def rotz4(th):
    return np.array([[np.cos(th), -np.sin(th), 0, 0],
                     [np.sin(th),  np.cos(th), 0, 0],
                     [0,           0,          1, 0],
                     [0,           0,          0, 1]])

def trans3(x, y):
    return np.array([[1, 0, x],
                     [0, 1, y],
                     [0, 0, 1]])

def trans4(x, y, z=0):
    return np.array([[1, 0, 0, x],
                     [0, 1, 0, y],
                     [0, 0, 1, z],
                     [0, 0, 0, 1]])


def persp_div(v):
    return v / v[-1]

def frustum(left, right, bottom, top, near, far):
    return np.array([
        [2*near/(right-left), 0, (right+left)/(right-left), 0],
        [0, 2*near/(top-bottom), (top+bottom)/(top-bottom), 0],
        [0, 0, -(far+near)/(far-near), -2*far*near/(far-near)],
        [0, 0, -1, 0]])

def perspective(fovy, aspect, near, far):
    f = 1/math.tan(fovy/2)
    return np.array([
        [f/aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, -(far+near)/(far-near), -2*far*near/(far-near)],
        [0, 0, -1, 0]])

def ortho(left, right, bottom, top, near, far):
    return np.array([
        [2/(right-left), 0, 0, -(right+left)/(right-left)],
        [0, 2/(top-bottom), 0, -(top+bottom)/(top-bottom)],
        [0, 0, -2/(far-near), -(far+near)/(far-near)],
        [0, 0, 0, 1]])

def look_at(eye, center, up):
    eye, center, up = map(np.asarray, (eye, center, up))
    f = normalize(center - eye)
    s = normalize(np.cross(f, up))
    u = normalize(np.cross(s, f))
    return np.array([[ s[0],  s[1],  s[2], -eye[0]],
                     [ u[0],  u[1],  u[2], -eye[1]],
                     [-f[0], -f[1], -f[2], -eye[2]],
                     [ 0,     0,     0,     1]])
