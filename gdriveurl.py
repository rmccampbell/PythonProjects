#!/usr/bin/env python3
import sys, re

def gdrive_dl_url(url):
    id = re.match('https://drive.google.com/file/d/([^/]+)/', url).group(1)
    return f'https://drive.google.com/uc?export=download&id={id}'

if __name__ == '__main__':
    for url in sys.argv[1:]:
        print(gdrive_dl_url(url))
