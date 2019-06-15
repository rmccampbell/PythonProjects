"""Allows scroll-based zooming in MPL"""

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import numpy as np

def zoom_scroll(event):
    if not event.inaxes:
        return
    axes = event.inaxes
    canvas = axes.figure.canvas
    toolbar = canvas.toolbar
    if hasattr(toolbar, '_nav_stack') and toolbar._nav_stack() is None:
        toolbar.push_current()

    xscale = yscale = 1.25 ** min(max(event.step, -10), 10)
    if event.key == 'x':
        yscale = 1.
    elif event.key == 'y':
        xscale = 1.

    scale = np.array([xscale, yscale])
    point = np.array([event.x, event.y])
    old = axes.viewLim.transformed(axes.transData)
    new = Bbox((old - point) / scale + point)
    lim = new.transformed(axes.transData.inverted())
    axes.set_xlim(*lim.intervalx)
    axes.set_ylim(*lim.intervaly)

    toolbar.push_current()
    canvas.draw()

def connect(canvas=None):
    if canvas:
        canvas.mpl_connect('scroll_event', zoom_scroll)
    else:
        plt.connect('scroll_event', zoom_scroll)

if __name__ == '__main__':
    connect()
    plt.plot(np.random.randint(0, 10, 10))
    plt.show()
