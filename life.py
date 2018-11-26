#!/usr/bin/env python3
import sys, os
import pygame
from pygame.locals import *
import numpy as np
import argparse

FPS = 30
SPEEDS = [2, 10, 30]

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

class Life:
    def __init__(self, seed=None, w=None, h=None, xoff=None, yoff=None,
                 screen=None, pixel=PIXEL, wrap=False, pause=False):
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
        self.speed = SPEEDS[1]
        self.px = pixel
        self.wrap = wrap
        self.paused = pause

        pygame.init()

        if screen is None:
            vi = pygame.display.Info()
            if self.width*self.px < vi.current_w and \
               self.height*self.px < vi.current_h:
                self.swidth = self.width
                self.sheight = self.height
            else:
                self.swidth = SWIDTH//self.px
                self.sheight = SHEIGHT//self.px
        else:
            self.swidth, self.sheight = screen

        self.screen = pygame.display.set_mode(
            (self.px*self.swidth, self.px*self.sheight), RESIZABLE)
        pygame.key.set_repeat(300, 50)
        self.display()

    def run(self):
        clock = pygame.time.Clock()
        i = 0
        self.running = True
        while self.running:
            clock.tick(FPS)
            redraw = False
            step = False

            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN:
                    scrl = SCRLSPD
                    if event.mod & KMOD_CTRL:
                        scrl *= 10
                    if event.key == K_ESCAPE or \
                       event.key == K_F4 and event.mod & KMOD_ALT:
                        self.running = False
                    elif event.key == K_SPACE:
                        self.speed = SPEEDS[(SPEEDS.index(self.speed) + 1)
                                           % len(SPEEDS)]
                    elif event.key == K_RETURN:
                        step = True
                    elif event.key == K_p:
                        self.paused = not self.paused
                    elif event.key == K_UP:
                        self.scrolly = max(self.scrolly - scrl, 0)
                        redraw = True
                    elif event.key == K_DOWN:
                        self.scrolly = max(min(self.scrolly + scrl,
                                               self.height - self.sheight), 0)
                        redraw = True
                    elif event.key == K_LEFT:
                        self.scrollx = max(self.scrollx - scrl, 0)
                        redraw = True
                    elif event.key == K_RIGHT:
                        self.scrollx = max(min(self.scrollx + scrl,
                                               self.width - self.swidth), 0)
                        redraw = True
                    elif event.key == K_HOME:
                        self.scrollx = 0
                        redraw = True
                    elif event.key == K_PAGEUP:
                        self.scrolly = 0
                        redraw = True
                    elif event.key == K_END:
                        self.scrollx = max(self.width - self.swidth, 0)
                        redraw = True
                    elif event.key == K_PAGEDOWN:
                        self.scrolly = max(self.height - self.sheight, 0)
                        redraw = True
                    elif event.key == K_EQUALS:
                        self.zoom(1)
                        redraw = True
                    elif event.key == K_MINUS:
                        self.zoom(-1)
                        redraw = True
                elif event.type == VIDEORESIZE:
                    px = self.px
                    self.swidth = sw = int(round(event.w / px))
                    self.sheight = sh = int(round(event.h / px))
                    if abs(sw - self.width) < 5:
                        self.swidth = sw = self.width
                    if abs(sh - self.height) < 5:
                        self.sheight = sh = self.height
                    self.scrolly = max(min(self.scrolly, self.height - sh), 0)
                    self.scrollx = max(min(self.scrollx, self.width - sw), 0)
                    pygame.display.set_mode((px*sw, px*sh), RESIZABLE)
                    redraw = True

            if i >= FPS//self.speed or step:
                i = 0
                if not self.paused or step:
                    self.tick()
                    redraw = True
            if redraw:
                self.display()
            i += 1

    def zoom(self, amount):
        oldpx = self.px
        self.px = px = max(oldpx + amount, 1)
        self.swidth = sw = int(round(self.swidth * oldpx / px))
        self.sheight = sh = int(round(self.sheight * oldpx / px))
        self.scrolly = max(min(self.scrolly, self.height - sh), 0)
        self.scrollx = max(min(self.scrollx, self.width - sw), 0)
        pygame.display.set_mode((px*sw, px*sh), RESIZABLE)

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
        px = self.px
        if self.width < self.swidth or self.height < self.sheight:
            self.screen.fill(BGCOLOR)
            self.screen.fill(COLOR0, (0, 0, self.width*px, self.height*px))
        else:
            self.screen.fill(COLOR0)
        for i in range(min(self.swidth, self.width)):
            for j in range(min(self.sheight, self.height)):
                if self.board[i + self.scrollx, j + self.scrolly]:
                    self.screen.fill(COLOR1, (i*px, j*px, px, px))
        pygame.display.flip()


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


def run(seed=None, w=None, h=None, xoff=0, yoff=0, screen=None, pixel=4,
        nowrap=False, pause=False):
    Life(seed, w, h, xoff, yoff, screen, pixel, nowrap, pause).run()


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        usage='%(prog)s [-h] [-s W H] [-x PIXEL] [-w] [-p] '
        '[file] [w h] [xoff yoff]')
    p.add_argument('-s', '--screen', metavar=('W', 'H'), type=int, nargs=2)
    p.add_argument('-x', '--pixel', type=int, default=PIXEL)
    p.add_argument('-w', '--wrap', action='store_true')
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
        run(file, w, h, xoff, yoff, ns.screen, ns.pixel, ns.wrap, ns.pause)
    finally:
        pygame.display.quit()
