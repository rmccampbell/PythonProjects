#!/usr/bin/env python3
import sys, os, argparse, urllib.request, re, mimetypes

CHUNK = 0x4000

exts = 'mp4|mov|flv|webm|ogg'
pattern = r'["=](http[^";?]*\.(?:%s)\b[^";]*)(?:"|&amp;)' % exts

def main(url, file=None, num=None, lst=False):
    if '://' not in url:
        url = 'http://' + url
    url = urllib.parse.unquote(url)
    res = urllib.request.urlopen(url)
    if res.headers.get_content_type() == 'text/html':
        if num is not None and not lst:
            print('Fetching video url #%d from %s...' % (num, url))
        en = res.headers.get_content_charset('iso-8859-1')
        html = res.read().decode(en)
        urls = []
        for m in re.finditer(pattern, html):
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
                lst = True
        if lst:
            print('Videos found at %s:' % url)
            for i, u in enumerate(urls):
                print('%d: %s' % (i, u))
            n = input('Download video #: ')
            if not n:
                return
            num = int(n)
        try:
            url = urls[num]
        except IndexError:
            print('Video #%d could not be found at %s' % (num, url))
            return
        print('Found video:', url)
        res = urllib.request.urlopen(url)

    if file is None or os.path.isdir(file):
        fname = (res.headers.get_filename() or
                 os.path.basename(urllib.parse.urlparse(url).path) or
                 'video')
        if not os.path.splitext(fname)[1]:
            mime = res.headers.get_content_type()
            fname = fname + mimetypes.guess_extension(mime)
        if file:
            file = os.path.join(file, fname)
        else:
            file = fname
    while os.path.exists(file):
        if input('File "%s" exists. Overwrite? (y/[n]) ' % file) != 'y':
            file = input('File name: ')
            if not file: return
        else:
            break

    print('Downloading "%s" to "%s"' % (url, file))
    f = open(file, 'wb')
    size = int(res.headers.get('Content-Length', 0))
    sizefmt = str(size>>20) if size else '?'
    amt = 0
    print('Starting download...')
    try:
        while True:
            bts = res.read(CHUNK)
            if not bts:
                break
            amt += f.write(bts)
            print('\rDownloaded: %d/%s MB' % (amt>>20, sizefmt), end='')

    except KeyboardInterrupt:
        print('\nDownload interupted')
    else:
        print('\nDownload finished')
    finally:
        f.close()
        res.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('file', nargs='?')
    p.add_argument('-n', '--vidnum', type=int)
    p.add_argument('-l', '--list', action='store_true')
    args = p.parse_args()
    main(args.url, args.file, args.vidnum, args.list)
