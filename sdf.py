import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import norm
from functools import reduce

def dot(xy1, xy2):
    return np.sum(np.multiply(xy1, xy2), -1)

def length2(xy):
    return dot(xy, xy)

def length(xy):
    return norm(xy, axis=-1)

def grid(x0=-10, x1=10, xn=1001, y0=-10, y1=10, yn=1001):
    x, y = np.meshgrid(np.linspace(x0, x1, xn), np.linspace(y0, y1, yn))
    return np.dstack((x, y))

def splitxy(xy):
    return xy[..., 0], xy[..., 1]

def get_extent(xy):
    x, y = xy[..., 0], xy[..., 1]
    x0, x1 = x.min(), x.max()
    y0, y1 = y.min(), y.max()
    dx = (x1 - x0) / (x.shape[1] - 1)
    dy = (y1 - y0) / (y.shape[0] - 1)
    return [x0-dx/2, x1+dx/2, y0-dy/2, y1+dy/2]

def draw_udf(xy, z, cmap='gray', contour=False, contourc='blue'):
    x, y = xy[..., 0], xy[..., 1]
    plt.clf()
    plt.imshow(z, cmap=cmap, vmin=0, origin='lower', extent=get_extent(xy))
    plt.colorbar()
    if contour:
        plt.contour(x, y, z, colors=contourc)

def draw_sdf(xy, z, cmap='bwr_r', contour=False, contourc='black'):
    x, y = xy[..., 0], xy[..., 1]
    plt.clf()
    vmax = abs(z).max()
    plt.imshow(z, cmap=cmap, vmin=-vmax, vmax=vmax, origin='lower',
               extent=get_extent(xy))
    plt.colorbar()
    if contour:
        plt.contour(x, y, z, colors=contourc)

def draw_grad(xy, z, spacing=100):
    x, y = xy[..., 0], xy[..., 1]
    gy, gx = np.gradient(z)
    s = spacing
    plt.quiver(x[::s,::s], y[::s,::s], gx[::s,::s], gy[::s,::s], angles='xy')

def circle(xy, r):
    return length(xy) - r

def box(xy, wh):
    d = abs(xy) - wh
    return length(np.maximum(d, 0)) + np.minimum(np.amax(d, axis=-1), 0)

def ubox(xy, wh):
    d = abs(xy) - wh
    return length(np.maximum(d, 0))

def union(*objs):
    return reduce(np.minimum, objs)

def intersect(*objs):
    return reduce(np.maximum, objs)

def sub(a, b):
    return np.maximum(a, -b)
