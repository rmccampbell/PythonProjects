#!/usr/bin/env python3
import socket
import urllib.parse

REQUEST = '''\
{} {} HTTP/1.1
Accept-Encoding: identity
User-Agent: httpget.py/1.0
Host: {}
Connection: close

'''.replace('\n', '\r\n')

def get(url, head=False):
    if '//' not in url:
        url = 'http://' + url
    split = urllib.parse.urlsplit(url)
    host = split.hostname
    port = split.port or 80
    path = split.path or '/'
    method = 'HEAD' if head else 'GET'
    s = socket.create_connection((host, port))
    s.send(REQUEST.format(method, path, split.netloc).encode('ascii'))
    with s.makefile('rb') as f:
        return f.read()

def getheaders(url):
    raw = get(url, True)
    headers = raw[:raw.find(b'\r\n\r\n')+2]
    return headers

def getbody(url, encoding=None):
    raw = get(url)
    body = raw[raw.find(b'\r\n\r\n')+4:]
    if encoding:
        body = body.decode(encoding)
    return body

if __name__ == '__main__':
    import sys
    raw = '-r' in sys.argv and (sys.argv.remove('-r') or True)
    headers = '-h' in sys.argv and (sys.argv.remove('-h') or True)
    if raw:
        sys.stdout.buffer.write(get(*sys.argv[1:], headers))
    elif headers:
        sys.stdout.buffer.write(getheaders(*sys.argv[1:]))
    else:
        body = getbody(*sys.argv[1:])
        if isinstance(body, bytes):
            sys.stdout.buffer.write(body)
        else:
            sys.stdout.write(body)
