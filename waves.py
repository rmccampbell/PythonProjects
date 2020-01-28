#!/usr/bin/env python3
import sys
import math
import argparse
import numpy as np
import pygame as pg
# import pygame.gfxdraw

# TODO: Add drawable barriers

FPS = 40

PIX = 2
WIDTH = 350
HEIGHT = 300
CLAMP = True
WRAP = False
DAMP_EDGE = 0

K = 0.2
DAMPING = .002
EDGE_DAMPING = .2
MAXVAL = 10
MINVAL = -10
DIAG = .4
SPLASH = 100
BALLACCEL = 1

COLOR0 = np.array([255, 255, 255])
COLOR1 = np.array([0, 0, 255])
BALLCOLOR = np.array([255, 0, 0])

def propagate(z, v, damping, clamp=CLAMP, wrap=WRAP):
    pad = np.pad(z, 1, 'wrap' if wrap else 'constant' if clamp else 'edge')
    a = (
        pad[:-2, 1:-1] + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]
        + (pad[:-2, :-2] + pad[2:, :-2] + pad[2:, 2:] + pad[:-2, 2:]) * DIAG
        - (4 + 4*DIAG) * z
    )*K - v*damping
    v += a
    z += v

def update_balls(z, balls, wrap=WRAP):
    gradz = np.dstack(np.gradient(z * BALLACCEL))
    size = np.array(z.shape)
    for i, xy in enumerate(balls):
        xind, yind = np.clip(xy.astype(int), 0, size-1)
        xy += gradz[xind, yind]
        if wrap:
            xy %= size
        else:
            xy = np.clip(xy, 0, size)
        balls[i] = xy

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
    balls.append(np.array([px / PIX, py / PIX], float))

def noise(width, height):
    return np.random.normal(0, .5, (width, height))

def clear(z, v, balls):
    v[:] = 0
    z[:] = noise(*z.shape)
    balls.clear()

def main(width=WIDTH, height=HEIGHT, clamp=CLAMP, wrap=WRAP,
         damp_edge=DAMP_EDGE):
    wrap = '-w' in sys.argv[1:] or WRAP
    z = np.zeros((width, height))
    v = np.zeros((width, height))

    damping = DAMPING
    if damp_edge:
        ramp = np.pad(np.zeros(np.array(z.shape)-2*damp_edge), damp_edge,
                      mode='linear_ramp', end_values=1)
        damping = ramp**2*(EDGE_DAMPING - DAMPING) + DAMPING

    balls = []
    clear(z, v, balls)
    screen = pg.display.set_mode((PIX*width, PIX*height))
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
        propagate(z, v, damping, clamp, wrap)
        draw(screen, z)
        if balls:
            update_balls(z, balls, wrap)
            draw_balls(screen, balls)
        pg.display.flip()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('width', nargs='?', type=int, default=WIDTH)
    p.add_argument('height', nargs='?', type=int, default=HEIGHT)
    p.add_argument('-C', '--no-clamp', dest='clamp',
                   action='store_false', default=CLAMP)
    p.add_argument('-w', '--wrap', action='store_true', default=WRAP)
    p.add_argument('-d', '--damp-edge', type=int, default=DAMP_EDGE)
    args = p.parse_args()
    try:
        main(args.width, args.height, clamp=args.clamp, wrap=args.wrap,
             damp_edge=args.damp_edge)
    finally:
        pg.quit()
