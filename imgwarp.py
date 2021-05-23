import numpy as np
##from scipy.ndimage import map_coordinates

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
        A = np.asarray(func)
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
##    out[dsty, dstx] = map_coordinates(img, (srcy, srcx))
    return out
