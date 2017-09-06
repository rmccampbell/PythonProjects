import numpy as np

def warp(img, func, scale=(1, 1), clip=False, wrap=False, reflect=False):
    w, h, *rest = img.shape
    dim = round(w*scale[0]), round(h*scale[1])
    dstx, dsty = np.indices(dim)
    srcx, srcy = func(dstx, dsty)
    srcx = srcx.round().astype(int)
    srcy = srcy.round().astype(int)
    if reflect:
        srcx %= 2*w
        srcy %= 2*h
        xmask = srcx >= w
        srcx[xmask] = 2*w - 1 - srcx[xmask]
        ymask = srcy >= h
        srcy[ymask] = 2*h - 1 - srcy[ymask]
    elif wrap:
        srcx %= w
        srcy %= h
    elif clip:
        srcx = srcx.clip(0, w - 1)
        srcy = srcy.clip(0, h - 1)
    else:
        mask = ((srcx >= 0) & (srcx < w) & (srcy >= 0) & (srcy < h))
        dstx, dsty = dstx[mask], dsty[mask]
        srcx, srcy = srcx[mask], srcy[mask]
    out = np.zeros(dim + tuple(rest), img.dtype)
    out[dstx, dsty] = img[srcx, srcy]
    return out

