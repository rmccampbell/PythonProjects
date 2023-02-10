#!/usr/bin/python3

import sys, os, random
import pygame as pg

DIR = os.path.dirname(sys.argv[0])

TICK = 50

GRIDW, GRIDH = 16, 16
GRIDSIZE = 24
XMARGIN = 16
TOPMARGIN = 48
BOTMARGIN = 16
WINW = GRIDW*GRIDSIZE + XMARGIN*2
WINH = GRIDH*GRIDSIZE + TOPMARGIN + BOTMARGIN

NMINES = 40

BGCOLOR = (192, 192, 192)
OVERCOLOR = (192, 192, 192)
UNDERCOLOR = (128, 128, 128)
LINECOLOR = (64, 64, 64)
TXTCOLOR = (0, 0, 0)

MINE = 1<<0
FLAG = 1<<1
COVERED = 1<<2

def load_image(name, convert=True):
    path = os.path.join(DIR, 'images/minesweeper', name + '.png')
    img = pg.image.load(path)
    if convert:
        img = img.convert_alpha()
    return img

def grid2pix(x, y):
    return x*GRIDSIZE + XMARGIN, y*GRIDSIZE + TOPMARGIN

def pix2grid(px, py):
    return (px - XMARGIN)//GRIDSIZE, (py - TOPMARGIN)//GRIDSIZE


class Images:
    def __init__(self):
        self.mine = load_image('mine')
        self.flag = load_image('flag')


class Minesweeper:
    def __init__(self):
        pg.init()
        pg.display.set_caption('Minesweeper')
        pg.display.set_icon(load_image('icon', False))
        self.screen = pg.display.set_mode((WINW, WINH))
        self.images = Images()
        self.font1 = pg.font.SysFont('Courier New', 24)
        self.running = False
        self.newgame()
        self.draw()
        pg.display.flip()

    def newgame(self):
        self.init_board()
        self.playing = True
        self.won = self.lost = False

    def clear_board(self):
        self.board = [[COVERED]*GRIDW for i in range(GRIDH)]

    def init_board(self):
        self.clear_board()
        for i in range(NMINES):
            x, y = random.randrange(GRIDW), random.randrange(GRIDH)
            while self.board[y][x] & MINE:
                x, y = random.randrange(GRIDW), random.randrange(GRIDH)
            self.board[y][x] |= MINE

    def run(self):
        self.running = True
        while self.running:
            self.events()
            self.update()
            self.draw()
            pg.display.flip()
            pg.time.wait(TICK)

    def update(self):
        pass

    def events(self):
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                self.running = False
            elif evt.type == pg.KEYDOWN:
                if evt.key == pg.K_F4 and evt.mod & pg.KMOD_ALT or \
                   evt.key == pg.K_ESCAPE:
                    self.running = False
                elif evt.key == pg.K_r:
                    self.newgame()
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if not self.playing:
                    self.newgame()
                else:
                    self.click(*evt.pos, evt.button)

    def click(self, px, py, button):
        x, y = pix2grid(px, py)
        if 0 <= x < GRIDW and 0 <= y < GRIDH:
            if button == pg.BUTTON_LEFT:
                if not self.board[y][x] & FLAG:
                    self.floodfill(x, y)
                    if self.board[y][x] & MINE:
                        self.board[y][x] &= ~COVERED
                        self.gameover()
                    else:
                        if self.check_win():
                            self.win()
            elif button == pg.BUTTON_RIGHT:
                if self.board[y][x] & COVERED:
                    self.board[y][x] ^= FLAG

    def floodfill(self, x, y):
        if not (0 <= x < GRIDW and 0 <= y < GRIDH):
            return
        if not self.board[y][x] & COVERED:
            return
        self.board[y][x] &= ~COVERED
        neighbors = self.count_neighbors(x, y)
        if neighbors == 0:
            self.floodfill(x+1, y)
            self.floodfill(x+1, y+1)
            self.floodfill(x, y+1)
            self.floodfill(x-1, y+1)
            self.floodfill(x-1, y)
            self.floodfill(x-1, y-1)
            self.floodfill(x, y-1)
            self.floodfill(x+1, y-1)

    def count_neighbors(self, x, y):
        neighbors = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                x2, y2 = x + i, y + j
                if (0 <= x2 < GRIDW and 0 <= y2 < GRIDH and
                        self.board[y2][x2] & MINE):
                    neighbors += 1
        return neighbors

    def check_win(self):
        for y in range(GRIDH):
            for x in range(GRIDW):
                cell = self.board[y][x]
                if cell & COVERED and not cell & MINE:
                    return False
        return True

    def win(self):
        print('You win!')
        self.playing = False
        self.won = True
        for y in range(GRIDH):
            for x in range(GRIDW):
                if self.board[y][x] & MINE:
                    self.board[y][x] |= FLAG

    def gameover(self):
        print('Game over!')
        self.playing = False
        self.lost = True
        for y in range(GRIDH):
            for x in range(GRIDW):
                if self.board[y][x] & MINE:
                    self.board[y][x] &= ~COVERED

    def draw(self):
        screen = self.screen
        screen.fill(BGCOLOR)
        face = '(⌐■_■)' if self.won else '(x_x)' if self.lost else '(•͜•)'
        # face = 'B-)' if self.won else 'X-P' if self.lost else ':-)'
        txtimg = self.font1.render(face, True, TXTCOLOR)
        txtrect = txtimg.get_rect(center=(WINW//2, TOPMARGIN//2))
        screen.blit(txtimg, txtrect)
        for y in range(GRIDH):
            for x in range(GRIDW):
                px, py = grid2pix(x, y)
                rect = pg.Rect(px, py, GRIDSIZE, GRIDSIZE)
                cell = self.board[y][x]
                if cell & COVERED:
                    pg.draw.rect(screen, OVERCOLOR, rect)
                else:
                    pg.draw.rect(screen, UNDERCOLOR, rect)
                    if cell & MINE:
                        screen.blit(self.images.mine, (px, py))
                    else:
                        neighbors = self.count_neighbors(x, y)
                        if neighbors:
                            txtimg = self.font1.render(
                                str(neighbors), True, TXTCOLOR)
                            txtrect = txtimg.get_rect(center=rect.center)
                            screen.blit(txtimg, txtrect)
                if cell & FLAG:
                    screen.blit(self.images.flag, (px, py))
                pg.draw.rect(screen, LINECOLOR, rect, 1)


if __name__ == '__main__':
    try:
        game = Minesweeper()
        game.run()
    finally:
        pg.quit()
