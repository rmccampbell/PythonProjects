#!/usr/bin/env python3
"""
Downloads videos from https://www.wcostream.com/
"""
import sys, os, subprocess, re, urllib.parse, json, base64, argparse
import requests
import pprint

def decode(codes, key):
    return ''.join(chr(int(re.sub(rb'\D', b'', base64.b64decode(s))) - key)
                   for s in codes)

def get_video_url(url, hd=False):
    resp = requests.get(url)
    resp.raise_for_status()
    match = re.search(r'var [a-zA-Z]{3} = (\[[^\]]+\])', resp.text)
    codes = json.loads(match.group(1))
    key = int(re.search(r'\) - (\d+)\);', resp.text).group(1))

    iframe = decode(codes, key)
    src = re.search(r'src="([^"]+)"', iframe).group(1)
    url2 = urllib.parse.urljoin(url, src)
##    print(url2)

    resp = requests.get(url2)
    resp.raise_for_status()
    urlre = r'get\("([^"]+)"\)\.then'
    url3 = re.search(urlre, resp.text).group(1)
    url3 = urllib.parse.urljoin(url2, url3)
##    print(url3)

    resp = requests.get(url3, headers={'X-Requested-With': 'XMLHttpRequest'})
    resp.raise_for_status()
    js = json.loads(resp.text)
##    ppring.pprint(js)
    vidurl = js['server'] + '/getvid?evid=' + (js['hd'] if hd else js['enc'])
##    print(vidurl)
##    resp2 = requests.head(vidurl, allow_redirects=True)
##    print(resp2)
##    pprint.pprint(resp2.headers)
    return vidurl

def url2file(url, restrict=False, default=''):
    path = urllib.parse.urlsplit(url).path
    path = urllib.parse.unquote(path)
    file = os.path.basename(path) or os.path.basename(os.path.dirname(path))
    if not file:
        return default
    if restrict:
        file = file.replace(' ', '_')
        file = re.sub(r'[^A-Za-z0-9_\-.]', '', file)
    return file

def get_filename(filename, url, orig_url=None, restrict=False):
    dir = None
    if filename and os.path.isdir(filename):
        dir, filename = filename, None
    if not filename:
        filename = url2file(url, restrict, 'video')
        if filename in ('video', 'getvid') and orig_url:
            filename = url2file(orig_url, restrict, 'video')
        if not os.path.splitext(filename)[1]:
            filename += '.mp4'
        if dir:
            filename = os.path.join(dir, filename)
    if os.path.exists(filename):
        overwrite = input('{} exists. Overwrite? (y/[n]) '.format(filename))
        if not overwrite.startswith('y'):
            return None
    return filename

def download(url, filename=None, orig_url=None, restrict=False, wget_params=()):
    filename = get_filename(filename, url, orig_url, restrict=False)
    if filename is None:
        return
    useragent = requests.utils.default_user_agent()
    subprocess.call(['wget', '-O', filename, '-U', useragent, url, *wget_params])

def get_size(url):
    resp = requests.head(url, allow_redirects=True)
    resp.raise_for_status()
    size = resp.headers.get('Content-Length')
    return size and int(size)

def human_readable(n, prec=1, strip=True):
    power = max((int(n).bit_length() - 1) // 10, 0)
    num = '{:.{}f}'.format(n / 1024**power, prec)
    if strip and '.' in num:
        num = num.rstrip('0').rstrip('.')
    return num + 'BKMGTPE'[power]


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-r', '--restrict', action='store_true')
    p.add_argument('-u', '--url-only', action='store_true')
    p.add_argument('-s', '--size', action='store_true')
    p.add_argument('-a', '--user-agent', action='store_true')
    p.add_argument('-H', '--high-def', action='store_true')
    p.add_argument('-w', '--wget-params', nargs=argparse.REMAINDER, default=[])
    p.add_argument('url')
    p.add_argument('filename', nargs='?')
    args = p.parse_args()
    vurl = get_video_url(args.url, args.high_def)
    if args.url_only:
        print(vurl)
    if args.size:
        size = get_size(vurl)
        print(human_readable(size) if size is not None else 'Unknown size')
    if args.user_agent:
        print(requests.utils.default_user_agent())
    if not (args.url_only or args.size):
        download(vurl, args.filename, orig_url=args.url, restrict=args.restrict,
                 wget_params=args.wget_params)
