#!/usr/bin/env python3
import argparse
import numpy as np
import matplotlib.pyplot as plt

def plot(*exprs, xlim=(-10, 10), ylim=None, axbox=False):
    ax = plt.gca()
    ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    if not axbox:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_position('zero')
        ax.spines['left'].set_position('zero')
        ax.tick_params(right=False, top=False, direction='inout')
    x = np.linspace(xlim[0], xlim[1], 1001)
    globs = vars(np).copy()
    locs = {'x': x, 't': x}
    for expr in exprs:
        y = eval(expr, globs, locs)
        plt.plot(x, y)
    plt.show()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('exprs', nargs='+')
    p.add_argument('-x', '--xlim', nargs=2, type=float, default=[-10, 10],
                   metavar=('XMIN', 'XMAX'))
    p.add_argument('-y', '--ylim', nargs=2, type=float,
                   metavar=('YMIN', 'YMAX'))
    p.add_argument('-b', '--axbox', action='store_true')
    args = p.parse_args()
    plot(*args.exprs, xlim=args.xlim, ylim=args.ylim, axbox=args.axbox)
