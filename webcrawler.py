#!/usr/bin/env python3
import sys
import re
import urllib.request, urllib.parse

def crawl(url, search, maxdepth=1, depth=0, seen=None):
    if seen is None:
        seen = {url}
    if '://' not in url:
        url = 'http://' + url
    with urllib.request.urlopen(url) as res:
        if res.headers.get_content_type() != 'text/html':
            return
        html = res.read().decode(res.headers.get_content_charset('latin-1'))

        if re.search(search, html, re.IGNORECASE):
            print(' ' * depth + url)
#        else:
#            print(' ' * depth + '### ' + url)
        if maxdepth and depth >= maxdepth:
            return

        links = re.findall(r'href="([^"]*)"', html, re.IGNORECASE)
        for lnk in links:
            lnk = urllib.parse.urldefrag(urllib.parse.urljoin(url, lnk)).url
            if lnk in seen:
                continue
            seen.add(lnk)
            try:
                crawl(lnk, search, maxdepth, depth+1, seen)
            except Exception as e:
                print('%s: %s' % (type(e).__name__, e))


if __name__ == '__main__':
    try:
        crawl(*sys.argv[1:3] + list(map(int, sys.argv[3:4])))
    except KeyboardInterrupt:
        pass
