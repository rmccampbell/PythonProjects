#!/usr/bin/env python3
import sys, os, errno, tempfile

def swap(file1, file2):
    if file1 == file2:
        raise ValueError("file names are the same")
    if not os.path.exists(file1):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file1)
    if not os.path.exists(file2):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file2)
    temp = tempfile.mktemp(suffix=os.path.basename(file1),
                           dir=os.path.dirname(file1))
    os.rename(file1, temp)
    os.rename(file2, file1)
    os.rename(temp, file2)

if __name__ == '__main__':
    try:
        swap(*sys.argv[1:])
    except Exception as e:
        sys.exit("error: %s" % e)
