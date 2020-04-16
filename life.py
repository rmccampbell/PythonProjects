#!/usr/bin/env python3
import sys, os
import pygame as pg
import numpy as np
import argparse

FPS = 60
SPEEDS = [2, 10, 30, 60]

BGCOLOR = (239, 239, 239)
COLOR0 = (255, 255, 255)
COLOR1 = (0, 0, 0)

SEED_FACTOR = .09

PIXEL = 4
WIDTH = 500
HEIGHT = 500
SWIDTH = 1200
SHEIGHT = 800

SCRLSPD = 10
BIGSCRL = 100

class Life:
    def __init__(self, seed=None, w=None, h=None, xoff=None, yoff=None, *,
                 ssize=None, pixel=PIXEL, wrap=False, speed=SPEEDS[1],
                 pause=False):
        if seed is None:
            seed = SEED_FACTOR
        elif isinstance(seed, str):
            try:
                seed = float(seed)
            except ValueError:
                pass
        if isinstance(seed, float):
            w, h = w or WIDTH, h or HEIGHT
            self.board = np.random.random((w, h)) < seed
        else:
            if isinstance(seed, str):
                if os.path.splitext(seed)[1] in ('.png', '.bmp'):
                    seed = parseimg(seed)
                else:
                    seed = parsetxt(seed)
            self.board = np.asarray(seed, bool)
            if w and h:
                temp = self.board
                w0, h0 = temp.shape
                # w, h = max(w, w0), max(h, h0)
                self.board = np.zeros((w, h), bool)
                if xoff is None:
                    xoff = (w - w0) // 2
                elif xoff < 0:
                    xoff += w
                if yoff is None:
                    yoff = (h - h0) // 2
                elif yoff < 0:
                    yoff += h
                xoff = min(max(0, xoff), w)
                yoff = min(max(0, yoff), h)
                self.board[xoff: xoff+w0, yoff: yoff+h0] = temp[:w-xoff, :h-yoff]
        self.width, self.height = self.board.shape
        self.scrollx = 0
        self.scrolly = 0
        self.speed = speed
        self.px = pixel
        self.wrap = wrap
        self.paused = pause

        pg.init()

        if ssize is None:
            vi = pg.display.Info()
            if self.width*self.px < vi.current_w and \
               self.height*self.px < vi.current_h:
                self.swidth = self.width
                self.sheight = self.height
            else:
                self.swidth = SWIDTH//self.px
                self.sheight = SHEIGHT//self.px
        else:
            self.swidth, self.sheight = ssize

        self.screen = pg.display.set_mode(
            (self.px*self.swidth, self.px*self.sheight), pg.RESIZABLE)
        pg.key.set_repeat(300, 50)
        self.display()

    def run(self):
        clock = pg.time.Clock()
        frame = 0
        self.running = True
        while self.running:
            clock.tick(FPS)
            redraw = False
            step = False

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                elif event.type == pg.KEYDOWN:
                    scrl = SCRLSPD
                    if event.mod & pg.KMOD_CTRL:
                        scrl = BIGSCRL
                    if event.key == pg.K_ESCAPE or \
                       event.key == pg.K_F4 and event.mod & pg.KMOD_ALT:
                        self.running = False
                    elif event.key == pg.K_SPACE:
                        self.speed = next(
                            (s for s in SPEEDS if s > self.speed), SPEEDS[0])
                    elif event.key == pg.K_RETURN:
                        step = True
                    elif event.key == pg.K_p:
                        self.paused = not self.paused
                    elif event.key == pg.K_UP:
                        self.scrolly = max(self.scrolly - scrl, 0)
                        redraw = True
                    elif event.key == pg.K_DOWN:
                        self.scrolly = max(min(self.scrolly + scrl,
                                               self.height - self.sheight), 0)
                        redraw = True
                    elif event.key == pg.K_LEFT:
                        self.scrollx = max(self.scrollx - scrl, 0)
                        redraw = True
                    elif event.key == pg.K_RIGHT:
                        self.scrollx = max(min(self.scrollx + scrl,
                                               self.width - self.swidth), 0)
                        redraw = True
                    elif event.key == pg.K_HOME:
                        self.scrollx = 0
                        redraw = True
                    elif event.key == pg.K_PAGEUP:
                        self.scrolly = 0
                        redraw = True
                    elif event.key == pg.K_END:
                        self.scrollx = max(self.width - self.swidth, 0)
                        redraw = True
                    elif event.key == pg.K_PAGEDOWN:
                        self.scrolly = max(self.height - self.sheight, 0)
                        redraw = True
                    elif event.key == pg.K_EQUALS:
                        self.zoom(1)
                        redraw = True
                    elif event.key == pg.K_MINUS:
                        self.zoom(-1)
                        redraw = True
                elif event.type == pg.VIDEORESIZE:
                    px = self.px
                    self.swidth = sw = int(round(event.w / px))
                    self.sheight = sh = int(round(event.h / px))
                    if abs(sw - self.width) < 5:
                        self.swidth = sw = self.width
                    if abs(sh - self.height) < 5:
                        self.sheight = sh = self.height
                    self.scrolly = max(min(self.scrolly, self.height - sh), 0)
                    self.scrollx = max(min(self.scrollx, self.width - sw), 0)
                    pg.display.set_mode((px*sw, px*sh), pg.RESIZABLE)
                    redraw = True

            frame += 1
            if frame >= FPS//self.speed or step:
                frame = 0
                if not self.paused or step:
                    self.tick()
                    redraw = True
            if redraw:
                self.display()

    def zoom(self, amount):
        oldpx = self.px
        self.px = px = max(oldpx + amount, 1)
        self.swidth = sw = int(round(self.swidth * oldpx / px))
        self.sheight = sh = int(round(self.sheight * oldpx / px))
        self.scrolly = max(min(self.scrolly, self.height - sh), 0)
        self.scrollx = max(min(self.scrollx, self.width - sw), 0)
        pg.display.set_mode((px*sw, px*sh), pg.RESIZABLE)

    def tick(self):
        #neighbors = convolve2d(self.board, [[1,1,1],[1,0,1],[1,1,1]], 'same')
        padded = np.pad(self.board, 1, 'wrap' if self.wrap else 'constant')
        neighbors = np.zeros_like(self.board, int)
        for di, dj in [(-1, -1), (-1, 0), (-1, 1), (0, 1),
                       (1, 1),   (1, 0),  (1, -1), (0, -1)]:
            neighbors += padded[1+di : self.width+1+di,
                                1+dj : self.height+1+dj]
        self.board[neighbors != 2] = False
        self.board[neighbors == 3] = True

    def display(self):
        pixels = np.full((self.swidth, self.sheight, 3), BGCOLOR, dtype=np.uint8)
        grid = self.board[self.scrollx: self.scrollx + self.swidth,
                          self.scrolly: self.scrolly + self.sheight]
        pixels[:self.width, :self.height] = np.where(grid[..., None], COLOR1, COLOR0)
        scaled = pixels.repeat(self.px, 0).repeat(self.px, 1)
        pg.surfarray.blit_array(self.screen, scaled)
        pg.display.flip()


def parsetxt(file):
    if isinstance(file, str):
        file = open(file) if file != '-' else sys.stdin
    lines = [line.rstrip('\n') for line in file]
    width = max(map(len, lines)) if lines else 0
    seed = [[c != ' ' for c in row.ljust(width)] for row in lines]
    return np.array(seed, bool, ndmin=2).T.copy()

def parseimg(file):
    from PIL import Image
    im = Image.open(file).convert('L')
    return (np.array(im) < 128).T.copy()


def run(seed=None, w=None, h=None, xoff=0, yoff=0, ssize=None, pixel=4,
        wrap=False, speed=SPEEDS[1], pause=False):
    Life(seed, w, h, xoff, yoff, ssize=ssize, pixel=pixel, wrap=wrap,
         speed=speed, pause=pause).run()


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        usage='%(prog)s [-h] [-s W H] [-x PIXEL] [-w] [-p] '
        '[file] [w h] [xoff yoff]')
    p.add_argument('-s', '--ssize', metavar=('W', 'H'), type=int, nargs=2)
    p.add_argument('-x', '--pixel', type=int, default=PIXEL)
    p.add_argument('-w', '--wrap', action='store_true')
    p.add_argument('-S', '--speed', type=int, default=SPEEDS[1])
    p.add_argument('-p', '--pause', action='store_true')
    p.add_argument('args', nargs='*', metavar='file, w, h, xoff, yoff')
    ns = p.parse_args()
    args = ns.args

    file, w, h, xoff, yoff = None, None, None, None, None
    if len(args) == 4 or len(args) > 5:
        p.error('wrong number of arguments')
    if len(args) == 5:
        xoff, yoff = map(int, args[3:])
        del args[3:]
    if len(args) in (1, 3):
        file = args[0]
    if len(args) in (2, 3):
        w, h = map(int, args[-2:])
    try:
        run(file, w, h, xoff, yoff, ssize=ns.ssize, pixel=ns.pixel,
            wrap=ns.wrap, speed=ns.speed, pause=ns.pause)
    finally:
        pg.display.quit()
