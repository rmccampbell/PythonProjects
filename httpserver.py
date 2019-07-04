#!/usr/bin/env python3
import sys, os, socket, datetime, mimetypes

CHUNKSIZE = 8192


def getline(file):
    return file.readline().decode().rstrip('\r\n')


def handle_get_head(rfile, wfile, path, headers, head=False):
    path = path.lstrip('/')
    try:
        file = open(path, 'rb')
    except OSError as e:
        print(e)
        wfile.write(b'HTTP/1.1 404 Not Found\r\n\r\n')
    else:
        with file:
            stat = os.stat(file.fileno())
            wfile.write(b'HTTP/1.1 200 OK\r\n')
            respheaders = {
                'Date': datetime.datetime.utcnow().ctime(),
                'Server': 'httpserver.py',
                'Content-Length': stat.st_size,
                'Content-Type':
                    mimetypes.guess_type(path)[0] or 'application/octet-stream',
                'Last-Modified':
                    datetime.datetime.utcfromtimestamp(stat.st_mtime).ctime(),
                'Connection': 'close',
            }
            for k, v in respheaders.items():
                wfile.write('{}: {}\r\n'.format(k, v).encode())
            wfile.write(b'\r\n')
            if not head:
                chunk = file.read(CHUNKSIZE)
                while chunk:
                    wfile.write(chunk)
                    chunk = file.read(CHUNKSIZE)


def handle(conn):
    rfile = conn.makefile('rb')
    wfile = conn.makefile('wb')
    req = getline(rfile)
    print('{}:{}: {}'.format(*conn.getpeername(), req))
    method, path, version = req.split()
    headers = {}
    line = getline(rfile)
    while line:
        key, value = line.split(':', 1)
        headers[key.strip().title()] = value.strip()
        line = getline(rfile)
    if method == 'GET':
        handle_get_head(rfile, wfile, path, headers)
    elif method == 'HEAD':
        handle_get_head(rfile, wfile, path, headers, True)
    else:
        wfile.write(b'HTTP/1.1 501 Method Not Implemented\r\n\r\n')


def serve(port=80):
    with socket.socket() as sock:
        sock.bind(('', port))
        sock.listen()
        print('Listening on {}:{}...'.format(*sock.getsockname()))
        while True:
            conn, addr = sock.accept()
            with conn:
                handle(conn)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    serve(port)
