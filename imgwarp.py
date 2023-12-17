import numpy as np
from scipy.ndimage import map_coordinates

def imgwarp(img, func, scale=1, center=False, clip=False, wrap=False,
            reflect=False):
    h, w, *rest = img.shape
    if np.isscalar(scale):
        scalew = scaleh = scale
    else:
        scalew, scaleh = scale
    dim2 = h2, w2 = round(h*scaleh), round(w*scalew)
    dsty, dstx = y, x = np.indices(dim2).reshape(2, -1)

    if center:
        y, x = y - (h2-1)/2, x - (w2-1)/2

    if isinstance(func, (list, np.ndarray)):
        A = np.asarray(func, float)
        if A.shape == (2, 2):
            src = A @ np.vstack((x, y))
            srcx, srcy = src
        else:
            src = A @ np.vstack((x, y, np.ones_like(x)))
            src /= src[2]
            srcx, srcy = src[:2]
    else:
        srcx, srcy = func(x, y)

    if center:
        srcy, srcx = srcy + (h-1)/2, srcx + (w-1)/2

    srcy = srcy.round().astype(int)
    srcx = srcx.round().astype(int)

    if reflect:
        srcy %= 2*h
        srcx %= 2*w
        ymask = srcy >= h
        srcy[ymask] = 2*h - 1 - srcy[ymask]
        xmask = srcx >= w
        srcx[xmask] = 2*w - 1 - srcx[xmask]
    elif wrap:
        srcy %= h
        srcx %= w
    elif clip:
        srcy.clip(0, h - 1, srcy)
        srcx.clip(0, w - 1, srcx)
    else:
        mask = ((srcy >= 0) & (srcy < h) & (srcx >= 0) & (srcx < w))
        dsty, dstx = dsty[mask], dstx[mask]
        srcy, srcx = srcy[mask], srcx[mask]

    out = np.zeros(dim2 + tuple(rest), img.dtype)
    out[dsty, dstx] = img[srcy, srcx]
    return out


def imgwarp_interp(img, func, scale=1, center=False, normalize=False, order=3,
                   mode='constant', cval=0.):
    h, w, *ext_dim = img.shape
    if np.isscalar(scale):
        scalew = scaleh = scale
    else:
        scalew, scaleh = scale
    h2, w2 = round(h*scaleh), round(w*scalew)
    dim2 = (h2, w2, *ext_dim)
    y, x, *ext_inds = np.indices(dim2).astype(float)

    if normalize:
        x = (x + .5) / w2
        y = (y + .5) / h2
        if center:
            x -= .5
            y -= .5
    elif center:
        x -= (w2-1)/2
        y -= (h2-1)/2

    if isinstance(func, (list, np.ndarray)):
        A = np.asarray(func, float)
        assert A.shape in ((2, 2), (3, 3))
        if A.shape == (2, 2):
            src = np.stack((x, y), -1) @ A.T
        else:
            src = np.stack((x, y, np.ones_like(x)), -1) @ A.T
            src /= src[..., 2:]
        srcx, srcy = src[..., 0], src[..., 1]
    else:
        srcx, srcy = func(x, y)

    if normalize:
        if center:
            x += .5
            y += .5
        srcx = srcx*w - .5
        srcy = srcy*h - .5
    elif center:
        srcx += (w-1)/2
        srcy += (h-1)/2

    return map_coordinates(img, (srcy, srcx, *ext_inds), order=order,
                           mode=mode, cval=cval)
