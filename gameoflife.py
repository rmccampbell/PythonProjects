#!/usr/bin/env python3
import sys, os
import pygame
from pygame.locals import *
import numpy as np
import argparse

FPS = 30
TPSS = [2, 10, 40]

BGCOLOR = (239, 239, 239)
COLOR0 = (255, 255, 255)
COLOR1 = (0, 0, 0)

INIT_FACTOR = .09

PIX = 5
WIDTH = 500
HEIGHT = 500
SWIDTH = 150
SHEIGHT = 130

SCRLSPD = 10

class Life:
    def __init__(self, seed=None, w=None, h=None, xoff=0, yoff=0,
                 nowrap=False, pause=False):
        if seed is None:
            w = w or WIDTH
            h = h or HEIGHT
            self.board = np.random.random((w, h)) < INIT_FACTOR
        else:
            if isinstance(seed, str):
                if os.path.splitext(seed)[1] in ('.png', '.bmp'):
                    seed = parseimg(seed)
                else:
                    seed = parsetxt(seed)
            self.board = temp = np.asarray(seed, bool)
            if w and h:
                self.board = np.zeros((w, h), bool)
                w1, h1 = temp.shape
                self.board[xoff: xoff+w1, yoff: yoff+h1] = temp[:w, :h]
        self.width, self.height = self.board.shape
        if self.width == 0 or self.height == 0:
            raise ValueError('seed has 0 size')
        self.swidth, self.sheight = SWIDTH, SHEIGHT
        self.scrollx = 0
        self.scrolly = 0
        self.tps = TPSS[1]
        self.wrap = not nowrap
        self.paused = pause

        pygame.init()
        self.screen = pygame.display.set_mode(
            (PIX*self.swidth, PIX*self.sheight), RESIZABLE)
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

            scrl = SCRLSPD
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN:
                    if event.mod & KMOD_CTRL:
                        scrl *= 10
                    if event.key == K_ESCAPE or \
                       event.key == K_F4 and event.mod & KMOD_ALT:
                        self.running = False
                    elif event.key == K_SPACE:
                        self.tps = TPSS[(TPSS.index(self.tps) + 1) % len(TPSS)]
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
                        if event.mod & KMOD_CTRL:
                            self.scrolly = 0
                        else:
                            self.scrollx = 0
                        redraw = True
                    elif event.key == K_END:
                        if event.mod & KMOD_CTRL:
                            self.scrolly = max(self.height - self.sheight, 0)
                        else:
                            self.scrollx = max(self.width - self.swidth, 0)
                        redraw = True
                elif event.type == VIDEORESIZE:
                    self.swidth = event.w // PIX
                    self.sheight = event.h // PIX
                    self.scrolly = max(min(self.scrolly,
                                           self.height - self.sheight), 0)
                    self.scrollx = max(min(self.scrollx,
                                           self.width - self.swidth), 0)
                    pygame.display.set_mode(
                        (PIX*self.swidth, PIX*self.sheight), RESIZABLE)
                    redraw = True

            if i >= FPS//self.tps or step:
                i = 0
                if not self.paused or step:
                    self.tick()
                    redraw = True
            if redraw:
                self.display()

            i += 1

    def tick(self):
        #neighbors = convolve2d(self.board, [[1,1,1],[1,0,1],[1,1,1]], 'same')
        expanded = np.pad(self.board, 1, 'wrap' if self.wrap else 'constant')
        neighbors = np.zeros_like(self.board, int)
        for di, dj in [(-1, -1), (0, -1), (1, -1), (1, 0),
                       (1, 1),   (0, 1),  (-1, 1), (-1, 0)]:
            neighbors += expanded[1+di : self.width+1+di,
                                  1+dj : self.height+1+dj]
        board2 = np.zeros_like(self.board)
        same = neighbors == 2
        board2[same] = self.board[same]
        board2[neighbors == 3] = True
        self.board = board2

    def display(self):
        if self.width < self.swidth or self.height < self.sheight:
            self.screen.fill(BGCOLOR)
            pygame.draw.rect(self.screen, COLOR0,
                             (0, 0, self.width*PIX, self.height*PIX))
        else:
            self.screen.fill(COLOR0)
        for i in range(min(self.swidth, self.width)):
            for j in range(min(self.sheight, self.height)):
                if self.board[i + self.scrollx, j + self.scrolly]:
                    pygame.draw.rect(self.screen, COLOR1,
                                     (i*PIX, j*PIX, PIX, PIX))
        pygame.display.flip()


def parsetxt(file):
    if isinstance(file, str):
        file = open(file) if file != '-' else sys.stdin
    lines = [line.rstrip('\n') for line in file]
    width = max(map(len, lines)) if lines else 0
    seed = [[c != ' ' for c in row.ljust(width)] for row in lines]
    return np.array(seed, int, ndmin=2).astype(bool).T.copy()

def parseimg(file):
    from PIL import Image
    im = Image.open(file)
    #im = im.convert('1', dither=Image.NONE)
    im = im.convert('L')
    a = (~np.array(im)//128).astype(bool).T
    return a


def run(seed=None, w=None, h=None, xoff=0, yoff=0, nowrap=False, pause=False):
    Life(seed, w, h, xoff, yoff, nowrap, pause).run()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-n', '--nowrap', action='store_true')
    p.add_argument('-p', '--pause', action='store_true')
    p.add_argument('args', nargs='*')
    ns = p.parse_args()
    args = ns.args

    file, w, h, xoff, yoff = None, None, None, 0, 0
    if len(args) == 4 or len(args) > 5:
        sys.exit('error: wrong number of arguments')
    if len(args) == 5:
        xoff, yoff = map(int, args[3:])
        del args[3:]
    if len(args) in (1, 3):
        file = args[0]
    if len(args) in (2, 3):
        w, h = map(int, args[-2:])
    try:
        run(file, w, h, xoff, yoff, nowrap=ns.nowrap, pause=ns.pause)
    finally:
        pygame.display.quit()
