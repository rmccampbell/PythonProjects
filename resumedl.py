#!/usr/bin/env python3
import sys, os, urllib.request

CHUNK = 0x4000

def resume(url, file):
    if isinstance(file, str):
        file = open(file, 'ab')
    with file:
        start = os.fstat(file.fileno()).st_size
        rang = 'bytes=%d-' % start
        req = urllib.request.Request(url, headers={'Range': rang})

        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            if e.code == 416:
                print('File already complete')
                return
            raise

        size = int(resp.headers.get('Content-Length', 0)) + start
        amt = start

        print('Downloading', url, 'starting from byte', start, 'to', file.name)
        with resp:
            try:
                bts = resp.read(CHUNK)
                while bts:
                    amt += file.write(bts)
                    print('\rDownloaded: %d/%s MB' %
                          (amt>>20, size>>20), end='')
                    bts = resp.read(CHUNK)

            except KeyboardInterrupt:
                print('\nDownload interupted')
            else:
                print('\nDownload finished')


if __name__ == '__main__':
    if len(sys.argv) < 3 or '-h' in sys.argv:
        sys.exit('usage: resumedl.py url file')
    resume(*sys.argv[1:])
