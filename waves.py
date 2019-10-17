#!/usr/bin/env python3
import sys
import math
import numpy as np
import pygame as pg
# import pygame.gfxdraw

FPS = 40

PIX = 2
WIDTH = 300
HEIGHT = 300
WRAP = False

K = 0.2
DAMPING = .002
MAXVAL = 10
MINVAL = -10
DIAG = .4
SPLASH = 100
BALLACCEL = 1

COLOR0 = np.array([255, 255, 255])
COLOR1 = np.array([0, 0, 255])
BALLCOLOR = (255, 0, 0)

def propagate(z, v, wrap=False):
    pad = np.pad(z, 1, 'wrap' if wrap else 'constant')
    a = (pad[:-2, 1:-1] + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]
         + (pad[:-2, :-2] + pad[2:, :-2] + pad[2:, 2:] + pad[:-2, 2:]) * DIAG
         - (4 + 4*DIAG) * z) * K - v * DAMPING
    v += a
    z += v

def update_balls(z, balls, wrap=False):
    dzdx, dzdy = np.gradient(z * BALLACCEL)
    for i, (x, y) in enumerate(balls):
        xind = math.floor(np.clip(x, 0, WIDTH-1))
        yind = math.floor(np.clip(y, 0, HEIGHT-1))
        x += dzdx[xind, yind]
        y += dzdy[xind, yind]
        if wrap:
            x, y = x % WIDTH, y % HEIGHT
        else:
            x, y = np.clip(x, 0, WIDTH), np.clip(y, 0, HEIGHT)
        balls[i] = (x, y)

def interp_colors(t, c0, c1):
    color = t[..., np.newaxis] * (c1 - c0) + c0
    return color.round().astype('uint8')

def draw(screen, z):
    norm = np.clip((z - MINVAL) / (MAXVAL - MINVAL), 0, 1)
    rgb = interp_colors(norm, COLOR0, COLOR1)
    pix = rgb.repeat(PIX, 0).repeat(PIX, 1)
    pg.surfarray.blit_array(screen, pix)

def draw_balls(screen, balls):
    for x, y in balls:
        px = math.floor(x * PIX)
        py = math.floor(y * PIX)
        # pg.gfxdraw.filled_circle(screen, px, py, 4, BALLCOLOR)
        pg.draw.circle(screen, BALLCOLOR, (px, py), 4)

def splash(z, v, down, px, py):
    x, y = px // PIX, py // PIX
    v[x, y] += -SPLASH if down else SPLASH

def add_ball(balls, px, py):
    balls.append((px // PIX, py // PIX))

def noise(width, height):
    return np.random.normal(0, .5, (width, height))

def clear(z, v, balls):
    v[:] = 0
    z[:] = noise(*z.shape)
    balls.clear()

def main():
    wrap = '-w' in sys.argv[1:] or WRAP
    z = np.zeros((WIDTH, HEIGHT))
    v = np.zeros((WIDTH, HEIGHT))
    balls = []
    clear(z, v, balls)
    screen = pg.display.set_mode((PIX*WIDTH, PIX*HEIGHT))
    draw(screen, z)
    clock = pg.time.Clock()
    running = True

    while running:
        mods = pg.key.get_mods()
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                running = False
            elif evt.type == pg.KEYDOWN:
                if evt.key == pg.K_ESCAPE or \
                   evt.key == pg.K_F4 and evt.mod & pg.KMOD_ALT or\
                   evt.key == pg.K_w and evt.mod & pg.KMOD_META:
                    running = False
                elif evt.key == pg.K_c:
                    clear(z, v, balls)
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if evt.button == 2 or mods & pg.KMOD_CTRL:
                    add_ball(balls, *evt.pos)
        mouse = pg.mouse.get_pressed()
        if (mouse[0] or mouse[2]) and not mods & pg.KMOD_CTRL:
            splash(z, v, mouse[0], *pg.mouse.get_pos())

        clock.tick(FPS)
        propagate(z, v, wrap)
        draw(screen, z)
        if balls:
            update_balls(z, balls, wrap)
            draw_balls(screen, balls)
        pg.display.flip()

if __name__ == '__main__':
    try:
        main()
    finally:
        pg.quit()
