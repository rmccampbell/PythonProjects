#!/usr/bin/env python3
import sys, copy, argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

params = {}

SMOOTHRAD = 8


def mandelbrot(bounds=(-2, 1, -1.2, 1.2), size=(1201, 961),
               maxiters=60, radius=2):
    x0, x1, y0, y1 = bounds
    c = (np.linspace(x0, x1, size[0])[None, :] +
         np.linspace(y0*1j, y1*1j, size[1])[:, None])
    z = c.copy()
    iters = np.ones(c.shape, int)
    mask = np.ones(c.shape, bool)
    zmask = z.ravel()
    rad2 = radius**2
    for i in range(1, maxiters):
        mask[mask] = zmask.real**2 + zmask.imag**2 < rad2
        iters[mask] += 1
        z[mask] = zmask = z[mask]**2 + c[mask]
    return np.ma.array(z, mask=mask), np.ma.array(iters, mask=mask)


def smooth_color(z, iters):
    return iters + 1 - np.ma.log2(np.ma.log2(abs(z)))


def draw_mandelbrot(bounds=(-2, 1, -1.2, 1.2), size=(1201, 961),
                    maxiters=80, smooth=False, radius=None,
                    cmap=None, interp='nearest'):
    params.update(bounds=bounds, size=size, maxiters=maxiters,
                  smooth=smooth, radius=radius, cmap=cmap, interp=interp)
    x0, x1, y0, y1 = bounds
    radius = radius or SMOOTHRAD if smooth else 2
    z, iters = mandelbrot(bounds, size, maxiters, radius)
    if smooth:
        iters = smooth_color(z, iters)
    cmap = copy.copy(plt.get_cmap(cmap))
    cmap.set_bad('black')
    dx = (x1 - x0) / (2 * (size[0] - 1))
    dy = (y1 - y0) / (2 * (size[1] - 1))
    plt.cla()
    plt.imshow(iters, cmap=cmap, interpolation=interp, norm=LogNorm(),
               origin='lower', extent=(x0-dx, x1+dx, y0-dy, y1+dy))
    plt.tight_layout()
    plt.draw()
    plt.show()


def on_click(event):
    if event.dblclick and event.inaxes and event.button in (1, 3):
        zoom(event.xdata, event.ydata, event.button == 1)


def zoom(x, y, zoom_in):
    scale = 2 ** (-1 if zoom_in else 1)
    x0, x1, y0, y1 = params.pop('bounds')
    x02, x12 = x + (x0 - x) * scale, x + (x1 - x) * scale
    y02, y12 = y + (y0 - y) * scale, y + (y1 - y) * scale
    canvas = plt.gcf().canvas
    canvas.toolbar.set_message('Recalculating...')
    canvas.flush_events()
    draw_mandelbrot((x02, x12, y02, y12), **params)
    canvas.toolbar.update()
    canvas.toolbar.set_message('')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-b', '--bounds', nargs=4, type=float,
                   default=(-2, 1, -1.2, 1.2), metavar=('X0', 'X1', 'Y0', 'Y1'),
                   help='default: %(default)s')
    p.add_argument('-s', '--size', nargs=2, type=int, default=(1201, 961),
                   metavar=('WIDTH', 'HEIGHT'), help='default: %(default)s')
    p.add_argument('-i', '--iters', type=int, default=80,
                   help='default: %(default)s')
    p.add_argument('-S', '--smooth', action='store_true')
    p.add_argument('-r', '--radius', type=int,
                   help='default: %d for smooth, 2 otherwise' % SMOOTHRAD)
    p.add_argument('-c', '--cmap')
    p.add_argument('-t', '--interp', default='nearest',
                   help='default: %(default)s')
    args = p.parse_args()
    try:
        import zoom_scroll
        zoom_scroll.connect()
    except ImportError:
        pass
    plt.connect('button_press_event', on_click)
    draw_mandelbrot(bounds=args.bounds, size=args.size, maxiters=args.iters,
                    radius=args.radius, smooth=args.smooth,
                    cmap=args.cmap, interp=args.interp)
