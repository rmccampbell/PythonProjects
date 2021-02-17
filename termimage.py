#!/usr/bin/env python3
import argparse
import numpy as np
from PIL import Image

UPPER_BLOCK = '▀'

def main(imagefile, width=None, height=None):
    img = Image.open(imagefile).convert('RGB')
    if width or height:
        width = width or round(height/img.size[1]*img.size[0])
        height = height or round(width/img.size[0]*img.size[1])
        img = img.resize((width, height))
    arr = np.asarray(img)
    for i in range(0, arr.shape[0], 2):
        for j in range(arr.shape[1]):
            ur, ug, ub = arr[i, j]
            print(f'\x1b[38;2;{ur};{ug};{ub}m', end='')
            if i+1 < arr.shape[0]:
                lr, lg, lb = arr[i+1, j]
                print(f'\x1b[48;2;{lr};{lg};{lb}m', end='')
            print(UPPER_BLOCK, end='')
        print('\x1b[0m')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('image')
    p.add_argument('-W', '--width', type=int)
    p.add_argument('-H', '--height', type=int)
    args = p.parse_args()
    main(args.image, args.width, args.height)
