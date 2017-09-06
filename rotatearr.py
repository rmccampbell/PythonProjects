import math, numpy as np

def _rotate(arr, theta):
    theta = math.radians(theta)
    c = math.cos(theta)
    s = math.sin(theta)
    h, w = arr.shape[:2]
    cy, cx = h//2, w//2
    w2 = round(w*abs(c) + h*abs(s))
    h2 = round(w*abs(s) + h*abs(c))
    cy2, cx2 = h2//2, w2//2
    arr2 = np.zeros((h2, w2) + arr.shape[2:], arr.dtype)
    for i in range(h2):
        for j in range(w2):
            y, x = i - cy2, j - cx2
            y1 = round(x*s + y*c)
            x1 = round(x*c - y*s)
            i1, j1 = y1 + cy, x1 + cx
            if 0 <= i1 < h and 0 <= j1 < w:
                arr2[i, j] = arr[i1, j1]
    return arr2

def rotate(arr, theta):
    theta = math.radians(theta)
    c = math.cos(theta)
    s = math.sin(theta)
    h, w = arr.shape[:2]
    cy, cx = h//2, w//2
    w2 = round(w*abs(c) + h*abs(s))
    h2 = round(w*abs(s) + h*abs(c))
    cy2, cx2 = h2//2, w2//2
    arr2 = np.zeros((h2, w2) + arr.shape[2:], arr.dtype)
    i, j = np.indices((h2, w2))
    y, x = i - cy2, j - cx2
    y1 = np.round(x*s + y*c).astype(int)
    x1 = np.round(x*c - y*s).astype(int)
    i1, j1 = y1 + cy, x1 + cx
    mask = (i1 >= 0) & (i1 < h) & (j1 >= 0) & (j1 < w)
    arr2[i[mask], j[mask]] = arr[i1[mask], j1[mask]]
    return arr2
