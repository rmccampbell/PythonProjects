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

    scale = 1.25 ** min(max(event.step, -10), 10)

    if axes.name == 'rectilinear':
        if event.key == 'x':
            scale = np.array([scale, 1.])
        elif event.key == 'y':
            scale = np.array([1., scale])
        point = np.array([event.x, event.y])
        old = axes.viewLim.transformed(axes.transData)
        new = Bbox((old - point) / scale + point)
        lim = new.transformed(axes.transData.inverted())
        axes.set_xlim(lim.intervalx)
        axes.set_ylim(lim.intervaly)
    elif axes.name == 'polar':
        axes.set_rmax(axes.get_rmax() / scale)
    elif axes.name == '3d':
        minx, maxx, miny, maxy, minz, maxz = axes.get_w_lims()
        df = 1/scale - 1
        dx = (maxx-minx)*df
        dy = (maxy-miny)*df
        dz = (maxz-minz)*df
        axes.set_xlim3d(minx - dx, maxx + dx)
        axes.set_ylim3d(miny - dy, maxy + dy)
        axes.set_zlim3d(minz - dz, maxz + dz)
        axes.get_proj()

    toolbar.push_current()
    canvas.draw_idle()


def connect(canvas=None):
    global _cid
    if canvas:
        _cid = canvas.mpl_connect('scroll_event', zoom_scroll)
    else:
        _cid = plt.connect('scroll_event', zoom_scroll)
    return _cid

def disconnect(cid=None, canvas=None):
    if cid is None:
        cid = _cid
    if canvas:
        canvas.mpl_disconnect(cid)
    else:
        plt.disconnect(cid)


if __name__ == '__main__':
    connect()
    plt.plot(np.random.randint(0, 10, 10))
    plt.show()
