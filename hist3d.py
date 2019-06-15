import matplotlib.pyplot as plt
import numpy as np

def hist3d(ax3d, x, y, bins=10, range=None, normed=False, weights=None,
           **kwargs):
    hist, xedges, yedges = np.histogram2d(x, y, bins, range, normed, weights)
    xpos, ypos = np.meshgrid(xedges[:-1], yedges[:-1])
    dx = np.broadcast_to(np.diff(xedges), xpos.shape)
    dy = np.broadcast_to(np.diff(yedges)[:, None], xpos.shape)
    return ax3d.bar3d(xpos.ravel(), ypos.ravel(), 0,
                      dx.ravel(), dy.ravel(), hist.T.ravel(), **kwargs)
