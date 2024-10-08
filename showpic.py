#!/usr/bin/env python3
import sys, os, glob, pygame, urllib.request, io, threading
from PIL import Image

IMG_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.webp'}

def load_img(url, scale=1, maxh=0, interp=Image.BICUBIC, base=None, cache={}):
    subcache = cache.setdefault((scale, maxh), set())
    if isinstance(url, pygame.Surface):
        if url in subcache:
            return url
        i = url
        w, h = url.get_size()
    elif isinstance(url, Image.Image):
        i = url
        w, h = url.size
    else:
        if 'bs4' in sys.modules:
            import bs4
            if isinstance(url, bs4.Tag):
                url = url['src']
        try:
            i = pygame.image.load(url)
        except (pygame.error, FileNotFoundError):
            url = urllib.parse.urljoin(base, url)
            req = urllib.request.Request(url, headers=
                                         {'User-Agent': 'Chrome'})
            with urllib.request.urlopen(req) as r:
                f = io.BytesIO(r.read())
            i = pygame.image.load(f, url)
        w, h = i.get_size()

    if scale != 1 or (maxh and maxh < h):
        if isinstance(i, pygame.Surface):
            i = Image.frombytes('RGBA', i.get_size(),
                                    pygame.image.tostring(i, 'RGBA'))
        w, h = int(w * scale), int(h * scale)
        if maxh and h > maxh:
            w, h = w * maxh // h, maxh
        if isinstance(interp, str):
            interp = getattr(Image, interp.upper())
        i = i.resize((w, h), interp)

    if isinstance(i, Image.Image):
        i = pygame.image.fromstring(i.tobytes(), i.size, i.mode)

    subcache.add(i)
    return i

def show_pic(url, scale=1, maxh=0, interp=Image.BICUBIC, blocking=True):
    i = load_img(url, scale, maxh, interp)
    pygame.init()
    s = pygame.display.set_mode(i.get_size(), pygame.RESIZABLE)
    s.fill((255, 255, 255))
    s.blit(i, (0, 0))
    pygame.display.flip()
    if blocking:
        try:
            running = True
            while running:
                for e in pygame.event.get():
                    if (e.type == pygame.QUIT or
                        e.type == pygame.KEYDOWN and
                          (e.key == pygame.K_ESCAPE or
                           e.key == pygame.K_F4 and e.mod & pygame.KMOD_ALT)):
                        running = False
        finally:
            pygame.display.quit()

def _load_async(imgs, scale, maxh, interp, url, can_load=None):
    for i, img in enumerate(imgs):
        if can_load: can_load.wait()
        try:
            imgs[i] = load_img(img, scale, maxh, interp, url)
        except Exception as e:
            print('%s: %s' % (type(e).__name__, e))

def gallery(imgs, scale=1, maxh=0, interp=Image.BICUBIC, base=None):
    imgs = list(imgs)
    threading.Thread(target=_load_async, args=(imgs, scale, maxh, interp, base),
                     daemon=True).start()

    try:
        i = 0
        running = True
        while running and imgs:
            img = imgs[i] = load_img(imgs[i], scale, maxh, interp, base)
            show_pic(img, scale, maxh, interp, False)
            waiting = True
            while waiting:
                for e in pygame.event.get():
                    if (e.type == pygame.QUIT or
                        e.type == pygame.KEYDOWN and
                          (e.key == pygame.K_ESCAPE or
                           e.key == pygame.K_F4 and e.mod & pygame.KMOD_ALT)):
                        waiting = False
                        running = False
                    elif e.type == pygame.KEYDOWN:
                        if e.key in (pygame.K_RETURN, pygame.K_RIGHT):
                            waiting = False
                            i = (i + 1) % len(imgs)
                        elif e.key == pygame.K_LEFT:
                            waiting = False
                            i = (i - 1) % len(imgs)
    finally:
        pygame.display.quit()

def web_gallery(url, begin=None, end=None, scale=1, maxh=0,
                interp=Image.BICUBIC):
    import bs4
    if '://' not in url:
        url = 'http://' + url
    req = urllib.request.Request(url, headers={'User-Agent': 'Chrome'})
    doc = bs4.BeautifulSoup(urllib.request.urlopen(req), 'lxml')
    imgs = [img for img in doc.find_all('img')[begin:end]
            if os.path.splitext(img['src'])[1] in IMG_EXTS]
    gallery(imgs, scale, maxh, url)

def linked_gallery(url, begin=None, end=None, scale=1, maxh=0,
                   interp=Image.BICUBIC, _close=True):
    import bs4
    if '://' not in url:
        url = 'http://' + url
    req = urllib.request.Request(url, headers={'User-Agent': 'Chrome'})
    doc = bs4.BeautifulSoup(urllib.request.urlopen(req), 'lxml')
    imgs = [img for img in doc.find_all('img')[begin:end]
            if os.path.splitext(img['src'])[1] in IMG_EXTS]
    links = [img.parent if img.parent.name == 'a' else None for img in imgs]

    can_load = threading.Event()
    can_load.set()
    threading.Thread(target=_load_async,
                     args=(imgs, scale, maxh, interp, url, can_load),
                     daemon=True).start()

    try:
        i = 0
        running = True
        while running and imgs:
            img = imgs[i] = load_img(imgs[i], scale, maxh, interp, url)
            show_pic(img, scale, maxh, interp, False)
            waiting = True
            while waiting:
                for e in pygame.event.get():
                    if (e.type == pygame.QUIT or
                        e.type == pygame.KEYDOWN and
                          (e.key == pygame.K_ESCAPE or
                           e.key == pygame.K_F4 and e.mod & pygame.KMOD_ALT)):
                        waiting = False
                        running = False
                    elif e.type == pygame.KEYDOWN:
                        if e.key in (pygame.K_RETURN, pygame.K_RIGHT):
                            waiting = False
                            i = (i + 1) % len(imgs)
                        elif e.key == pygame.K_LEFT:
                            waiting = False
                            i = (i - 1) % len(imgs)
                        elif e.key == pygame.K_SPACE and links[i]:
                            href = urllib.parse.urljoin(url, links[i]['href'])
                            can_load.clear()
                            if (os.path.splitext(href)[1] in IMG_EXTS):
                                try:
                                    show_pic(href, scale, maxh, interp)
                                except urllib.error.HTTPError as e:
                                    print(e)
                            else:
                                try:
                                    linked_gallery(href, None, None, scale,
                                                   maxh, interp, False)
                                except urllib.error.HTTPError as e:
                                    print(e)
                            can_load.set()
                            show_pic(img, scale, maxh, interp, False)
##                    elif e.type == pygame.VIDEORESIZE:
##                        print(e)
    finally:
        if _close: pygame.display.quit()
        can_load.clear()



if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('url', nargs='?')
    p.add_argument('-g', '--gallery', nargs='*')
    p.add_argument('-w', '--webgal', action='store_true')
    p.add_argument('-l', '--linkgal', action='store_true')
    p.add_argument('-s', '--scale', type=float, default=1)
    p.add_argument('-m', '--maxh', type=int, default=0)
    p.add_argument('-i', '--interp', choices=['nearest', 'bilinear', 'bicubic'],
                   default='bicubic')
    p.add_argument('-b', '--begin', type=int)
    p.add_argument('-e', '--end', type=int)
    args = p.parse_args()
    if args.url is None and args.gallery is None:
        args.url = input('URL or path: ')

    if args.linkgal:
        linked_gallery(args.url, args.begin, args.end, args.scale, args.maxh,
                       args.interp)
    elif args.webgal:
        web_gallery(args.url, args.begin, args.end, args.scale, args.maxh,
                    args.interp)
    elif args.gallery is not None:
        paths = args.gallery or [input('Path: ')]
        paths = [file for path in paths for file in glob.glob(path) or (path,)]
        if len(paths) == 1 and os.path.isdir(paths[0]):
            dir = paths[0]
            paths = []
            for f in os.listdir(dir):
                f = os.path.join(dir, f) 
                if os.path.isfile(f) and \
                   os.path.splitext(f)[1] in IMG_EXTS:
                    paths.append(f)
        gallery(paths, args.scale, args.maxh, args.interp)
    else:
        show_pic(args.url, args.scale, args.maxh, args.interp)
