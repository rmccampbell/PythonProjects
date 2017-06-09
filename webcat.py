#!/usr/bin/env python3
import sys, urllib.request

def webcat(url, ofile=None):
    if '://' not in url:
        url = 'http://' + url
    res = urllib.request.urlopen(url)
    bts = res.read()
    istext = res.headers.get_content_maintype() == 'text'
    if ofile:
        ofile = open(ofile, 'w' if istext else 'wb')
    else:
        ofile = sys.stdout if istext else sys.stdout.buffer
    if istext:
        en = res.headers.get_content_charset() or 'iso-8859-1'
        text = bts.decode(en).replace('\r\n', '\n')
        oen = ofile.encoding
        text = text.encode(oen, 'backslashreplace').decode(oen)
        ofile.write(text)
    else:
        ofile.write(bts)

if __name__ == '__main__':
    webcat(sys.argv[1] if len(sys.argv) > 1 else input('Url: '),
           sys.argv[2] if len(sys.argv) > 2 else None)
