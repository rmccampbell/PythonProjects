import math
import numpy as np
from numpy.linalg import inv, norm, matrix_power as powm
from numpy import pi

deg = pi / 180

I2 = np.eye(2)
I3 = np.eye(3)
I4 = np.eye(4)


def vec(a, n=4, homo=None):
    if homo is None:
        homo = n == 4
    if np.isscalar(a):
        a = (a,)*(n-1 if homo else n)
    a = np.asarray(a, float).ravel()
    if a.size < n:
        b = np.zeros(n)
        if homo:
            b[-1] = 1
        b[:a.size] = a
        return b
    elif a.size > n:
        return a[:n]
    return a

def vec2(x=0, y=None):
    if y is None:
        return vec(x, 2, False)
    return np.array([x, y], float)

def vec3(x=0, y=None, z=0):
    if y is None:
        return vec(x, 3, False)
    return np.array([x, y, z], float)

def vec3h(x=0, y=None, z=1):
    if y is None:
        return vec(x, 3, True)
    return np.array([x, y, z], float)

def vec4(x=0, y=None, z=0, w=1):
    if y is None:
        return vec(x, 4, True)
    return np.array([x, y, z, w], float)


def normalize(v):
    return v / norm(v)

def unit2(x, y=None):
    return normalize(vec2(x, y))

def unit3(x, y=None, z=0):
    return normalize(vec3(x, y, z))

def unit4(x, y=None, z=0, w=1):
    return normalize(vec4(x, y, z, w))


def mat(arr, n):
    if np.isscalar(arr):
        return arr * np.eye(n)
    arr = np.asarray(arr)
    if arr.shape == (n, n):
        return arr
    arr2 = np.eye(n)
    h, w = arr.shape
    arr2[:h, :w] = arr[:n, :n]
    return arr2

def mat2(arr=0):
    return mat(arr, 2)

def mat3(arr=0):
    return mat(arr, 3)

def mat4(arr=0):
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

rot3h = rotz3

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

def reflx2(a):
    return np.diag([-1, 1])

def refly2(a):
    return np.diag([1, -1])

def reflx3(a):
    return np.diag([-1, 1, 1])

def refly3(a):
    return np.diag([1, -1, 1])

def reflz3(a):
    return np.diag([1, 1, -1])

def reflx4(a):
    return np.diag([-1, 1, 1, 1])

def refly4(a):
    return np.diag([1, -1, 1, 1])

def reflz4(a):
    return np.diag([1, 1, -1, 1])


def skewx2(a):
    return np.array([[1, a], [0, 1]])

def skewy2(a):
    return np.array([[1, 0], [a, 1]])

def skewxy3(a):
    return np.array([[1, a, 0], [0, 1, 0], [0, 0, 1]])

def skewxz3(a):
    return np.array([[1, 0, a], [0, 1, 0], [0, 0, 1]])

def skewyx3(a):
    return np.array([[1, 0, 0], [a, 1, 0], [0, 0, 1]])

def skewyz3(a):
    return np.array([[1, 0, 0], [0, 1, a], [0, 0, 1]])

def skewzx3(a):
    return np.array([[1, 0, 0], [0, 1, 0], [a, 0, 1]])

def skewzy3(a):
    return np.array([[1, 0, 0], [0, 1, 0], [0, a, 1]])

skewx3h = skewxy3

skewy3h = skewyx3

def skewxy4(a):
    return mat4(skewxy3(a))

def skewxz4(a):
    return mat4(skewxz3(a))

def skewyx4(a):
    return mat4(skewyx3(a))

def skewyz4(a):
    return mat4(skewyz3(a))

def skewzx4(a):
    return mat4(skewzx3(a))

def skewzy4(a):
    return mat4(skewzy3(a))


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
