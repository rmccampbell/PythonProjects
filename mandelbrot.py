#!/usr/bin/env python3
import sys, copy, argparse
import numpy as np
from numpy import ma
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

params = {}

def mandelbrot(x0=-2, x1=1, y0=-1.2, y1=1.2, width=1201, height=961,
               maxiters=60):
    c = (np.linspace(x0, x1, width)[None, :] +
         np.linspace(y0*1j, y1*1j, height)[:, None])
    z = c.copy()
    iters = np.ones(c.shape, int)
    mask = np.ones(c.shape, bool)
    zmask = z.ravel()
    for i in range(1, maxiters):
        mask[mask] = zmask.real**2 + zmask.imag**2 < 4
        iters[mask] += 1
        z[mask] = zmask = z[mask]**2 + c[mask]
    return np.ma.array(iters, mask=mask)

def draw_mandelbrot(x0=-2, x1=1, y0=-1.2, y1=1.2, width=1201, height=961,
                    maxiters=80):
    params.update(x0=x0, x1=x1, y0=y0, y1=y1, width=width, height=height,
                  maxiters=maxiters)
    iters = mandelbrot(x0, x1, y0, y1, width, height, maxiters)
    cmap = copy.copy(plt.get_cmap())
    cmap.set_bad('black')
    dx = (x1 - x0) / (2 * (width - 1))
    dy = (y1 - y0) / (2 * (height - 1))
    plt.cla()
    plt.imshow(iters, cmap=cmap, interpolation='bilinear', norm=LogNorm(),
               origin='lower', extent=(x0-dx, x1+dx, y0-dy, y1+dy))
    plt.tight_layout()
    plt.draw()
    plt.show()

def on_click(event):
    if event.dblclick and event.inaxes and event.button in (1, 3):
        zoom(event.xdata, event.ydata, event.button == 1)

def zoom(x, y, zoom_in):
    scale = 2 ** (-1 if zoom_in else 1)
    x0, x1, y0, y1 = params['x0'], params['x1'], params['y0'], params['y1']
    x02, x12 = x + (x0 - x) * scale, x + (x1 - x) * scale
    y02, y12 = y + (y0 - y) * scale, y + (y1 - y) * scale
    # plt.gcf().canvas.toolbar.set_message('Recalculating...')
    draw_mandelbrot(x02, x12, y02, y12, params['width'], params['height'],
                    params['maxiters'])

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-b', '--bounds', nargs=4, type=float,
                   default=(-2, 1, -1.2, 1.2), metavar=('X0', 'X1', 'Y0', 'Y1'))
    p.add_argument('-d', '--dim', nargs=2, type=int,
                   default=(1201, 961), metavar=('WIDTH', 'HEIGHT'))
    p.add_argument('-i', '--iters', type=int, default=80)
    args = p.parse_args()
    try:
        import zoom_scroll
        zoom_scroll.connect()
    except:
        pass
    plt.connect('button_press_event', on_click)
    draw_mandelbrot(*args.bounds, *args.dim, args.iters)
