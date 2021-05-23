#!/usr/bin/env python3
import sys, os, argparse, urllib.request, urllib.parse, re, mimetypes

CHUNK = 0x4000

EXTS = 'mp4|mov|flv|webm|ogg'
PATTERN = r'["=](http[^";?]+\.(?:%s)\b[^";]*)(?:"|&amp;)'

def human_readable(n, prec=1, strip=True):
    power = max((int(n).bit_length() - 1) // 10, 0)
    num = '{:.{}f}'.format(n / 1024**power, prec)
    if strip and '.' in num:
        num = num.rstrip('0').rstrip('.')
    return num + 'BKMGTPE'[power]

def main(url, file=None, num=None, list_urls=False, url_only=False,
         force_download=False, size_only=False, exts=EXTS):
    url = urllib.parse.unquote(url)
    if '//' not in url:
        url = 'http://' + url
    method = 'HEAD' if size_only and force_download else 'GET'
    headers = {'User-Agent': 'Chrome'}
    req = urllib.request.Request(url, headers=headers, method=method)
    resp = urllib.request.urlopen(req)
    ctype = resp.headers.get_content_type()
    if not force_download and ctype == 'text/html':
        if num is not None and not list_urls and not url_only:
            print('Fetching video url #%d from %s...' % (num, url))
        en = resp.headers.get_content_charset('iso-8859-1')
        with resp:
            html = resp.read().decode(en)
        urls = []
        for m in re.finditer(PATTERN % exts, html):
            u = urllib.parse.unquote(m.group(1))
            u = urllib.parse.urljoin(url, u)
            if u not in urls:
                urls.append(u)
        if not urls:
            print('No videos found at', url)
            return
        if num is None:
            num = 0
            if len(urls) > 1:
                list_urls = True
        if list_urls:
            if not url_only:
                print('Videos found at %s:' % url)
            for i, u in enumerate(urls):
                print(u if url_only else '%d: %s' % (i, u))
            if url_only:
                return
            n = input('Download video #: ')
            if not n:
                return
            num = int(n)
        try:
            url = urls[num]
        except IndexError:
            print('Video #%d could not be found at %s' % (num, url))
            return
        if url_only:
            print(url)
            return
        print('Found video:', url)
        method = 'HEAD' if size_only else 'GET'
        req = urllib.request.Request(url, headers=headers, method=method)
        resp = urllib.request.urlopen(req)
    elif url_only:
        print(url)
        resp.close()
        return

    if size_only:
        size = int(resp.headers.get('Content-Length', -1))
        print(human_readable(size) if size >= 0 else 'unknown size')
        resp.close()
        return

    if file is None or os.path.isdir(file):
        fname = (resp.headers.get_filename() or
                 os.path.basename(urllib.parse.urlsplit(url).path) or
                 'video')
        if not os.path.splitext(fname)[1]:
            mime = resp.headers.get_content_type()
            if mime != 'text/plain':
                fname += mimetypes.guess_extension(mime)
        if file:
            file = os.path.join(file, fname)
        else:
            file = fname
    while os.path.exists(file):
        if input('File "%s" exists. Overwrite? (y/[n]) ' % file) != 'y':
            file = input('File name: ')
            if not file:
                return
        else:
            break

    print('Downloading "%s" to "%s"' % (url, file))
    size = int(resp.headers.get('Content-Length', -1))
    sizefmt = str(size >> 20) if size >= 0 else '?'
    amt = 0
    with open(file, 'wb') as file, resp:
        print('Starting download...')
        try:
            bts = resp.read(CHUNK)
            while bts:
                amt += file.write(bts)
                print('\rDownloaded: %d/%s MB' % (amt >> 20, sizefmt), end='')
                bts = resp.read(CHUNK)

        except KeyboardInterrupt:
            print('\nDownload interupted')
        else:
            print('\nDownload finished')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('file', nargs='?')
    p.add_argument('-n', '--vidnum', type=int)
    p.add_argument('-l', '--list', action='store_true')
    p.add_argument('-u', '--url-only', action='store_true')
    p.add_argument('-d', '--force-download', action='store_true')
    p.add_argument('-s', '--size', action='store_true')
    p.add_argument('-x', '--exts', default=EXTS)
    args = p.parse_args()
    try:
        main(args.url, args.file, args.vidnum, args.list, args.url_only,
             args.force_download, args.size, args.exts)
    except Exception as e:
        print('%s: %s' % (type(e).__name__, e))
