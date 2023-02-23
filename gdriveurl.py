#!/usr/bin/env python3
import re, argparse

def gdrive_direct_url(url, download=False):
    id = re.match('https://drive.google.com/file/d/([^/]+)/', url).group(1)
    if download:
        return f'https://drive.google.com/uc?export=download&id={id}'
    return f'https://drive.google.com/uc?id={id}'

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('urls', nargs='+')
    p.add_argument('-d', '--download', dest='download', action='store_true')
    args = p.parse_args()
    for url in args.urls:
        print(gdrive_direct_url(url, args.download))
