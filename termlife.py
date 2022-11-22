#!/usr/bin/env python3
import sys, os, time
import curses
import numpy as np
import argparse

FPS = 60
SPEEDS = [2, 10, 30, 60]
SPEED = SPEEDS[1]

SEED_FACTOR = .09

WIDTH = 200
HEIGHT = 200

SCRLSPD = 5
BIGSCRL = 50

class Life:
    def __init__(self, screen, seed=None, w=None, h=None, xoff=None, yoff=None,
                 wrap=False, speed=SPEED, pause=False):
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
        self.wrap = wrap
        self.paused = pause

        self.screen = screen
        curses.curs_set(0)
        screen.nodelay(True)
        self.sheight, self.swidth = screen.getmaxyx()
        self.sheight *= 2
        self.display()

    def run(self):
        i = 0
        self.running = True
        while self.running:
            time.sleep(1/FPS)
            redraw = False
            step = False

            while True:
                try:
                    key = self.screen.getkey()
                except curses.error:
                    break
                scrl = SCRLSPD
                if key in ('kUP5', 'kDN5', 'kLFT5', 'kRIT5',
                           'CTL_UP', 'CTL_DOWN', 'CTL_LEFT', 'CTL_RIGHT'):
                    scrl = BIGSCRL
                if key in ('\x1b', 'q', 'Q'):
                    self.running = False
                elif key == ' ':
                    self.speed = next(
                        (s for s in SPEEDS if s > self.speed), SPEEDS[0])
                elif key == '\n':
                    step = True
                elif key == 'p':
                    self.paused = not self.paused
                elif key in ('KEY_UP', 'kUP5', 'CTL_UP'):
                    self.scrolly = max(self.scrolly - scrl, 0)
                    redraw = True
                elif key in ('KEY_DOWN', 'kDN5', 'CTL_DOWN'):
                    self.scrolly = max(min(self.scrolly + scrl,
                                           self.height - self.sheight), 0)
                    redraw = True
                elif key in ('KEY_LEFT', 'kLFT5', 'CTL_LEFT'):
                    self.scrollx = max(self.scrollx - scrl, 0)
                    redraw = True
                elif key in ('KEY_RIGHT', 'kRIT5', 'CTL_RIGHT'):
                    self.scrollx = max(min(self.scrollx + scrl,
                                           self.width - self.swidth), 0)
                    redraw = True
                elif key == 'KEY_HOME':
                    self.scrollx = 0
                    redraw = True
                elif key == 'KEY_PPAGE':
                    self.scrolly = 0
                    redraw = True
                elif key == 'KEY_END':
                    self.scrollx = max(self.width - self.swidth, 0)
                    redraw = True
                elif key == 'KEY_NPAGE':
                    self.scrolly = max(self.height - self.sheight, 0)
                    redraw = True
                elif key == 'KEY_RESIZE':
                    self.sheight, self.swidth = self.screen.getmaxyx()
                    self.sheight *= 2
                    self.scrolly = max(min(self.scrolly,
                                           self.height - self.sheight), 0)
                    self.scrollx = max(min(self.scrollx,
                                           self.width - self.swidth), 0)
                    redraw = True

            i += 1
            if i >= FPS//self.speed or step:
                i = 0
                if not self.paused or step:
                    self.tick()
                    redraw = True
            if redraw:
                self.display()

    def tick(self):
        # neighbors = convolve2d(self.board, [[1,1,1],[1,0,1],[1,1,1]], 'same')
        padded = np.pad(self.board, 1, 'wrap' if self.wrap else 'constant')
        neighbors = np.zeros_like(self.board, int)
        for di, dj in [(-1, -1), (-1, 0), (-1, 1), (0, 1),
                       (1, 1),   (1, 0),  (1, -1), (0, -1)]:
            neighbors += padded[1+di : self.width+1+di,
                                1+dj : self.height+1+dj]
        self.board[neighbors != 2] = False
        self.board[neighbors == 3] = True

    def display(self):
        # self.screen.clear()
        grid = self.board[self.scrollx: self.scrollx + self.swidth,
                          self.scrolly: self.scrolly + self.sheight].T.tolist()
        chars = ' ▄▀█'
        for i in range(0, len(grid), 2):
            row1 = grid[i]
            row2 = grid[i+1] if i+1 < len(grid) else [False]*len(row1)
            line = [chars[2*x+y] for x, y in zip(row1, row2)]
            self.screen.addstr(i//2, 0, ''.join(line))
        self.screen.refresh()


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


def run(stdscr, seed=None, w=None, h=None, xoff=0, yoff=0,
        wrap=False, speed=SPEED, pause=False):
    Life(stdscr, seed, w, h, xoff, yoff, wrap=wrap, speed=speed, pause=pause
         ).run()


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        usage='%(prog)s [-h] [-w] [-p] '
        '[file] [w h] [xoff yoff]')
    p.add_argument('-w', '--wrap', action='store_true')
    p.add_argument('-s', '--speed', type=int, default=SPEED)
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
    curses.wrapper(run, file, w, h, xoff, yoff,
                   wrap=ns.wrap, speed=ns.speed, pause=ns.pause)
