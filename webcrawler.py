import sys
import re
import urllib.request, urllib.parse

def crawl(url, search, depth=0, maxdepth=10, seen=None):
    if '://' not in url:
        url = 'http://' + url
    if seen is None:
        seen = {url}
    if maxdepth and depth > maxdepth:
        return
    with urllib.request.urlopen(url) as res:
        if res.headers.get_content_type() != 'text/html':
            return
        html = res.read().decode('latin-1')

        if re.search(r'\b'+search+r'\b', html, re.IGNORECASE):
            print(url)
##        else:
##            print('\t' + url)
        for lnk in re.findall(r'href="([^"]*)"', html):
            lnk = urllib.parse.urljoin(url, lnk)
            parts = urllib.parse.urlparse(lnk)
            lnk = parts.scheme + "://" + parts.netloc + parts.path
            if lnk in seen:
                continue
            seen.add(lnk)
            try:
                crawl(lnk, search, depth+1, maxdepth, seen)
            except Exception as e:
                pass


if __name__ == '__main__':
    try:
        crawl(*sys.argv[1:])
    except KeyboardInterrupt:
        pass
