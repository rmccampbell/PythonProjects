#!/usr/bin/env python3
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

def update_balls(z, ballx, bally):
    dzdx, dzdy = np.gradient(z * BALLACCEL)
    xind = ballx.round().astype(int).clip(0, WIDTH-1)
    yind = bally.round().astype(int).clip(0, HEIGHT-1)
    ballx += dzdx[xind, yind]
    bally += dzdy[xind, yind]

def interp_color(z, c0, c1):
    color = z[..., np.newaxis] * (c1 - c0) + c0
    return color.round().astype('uint8')

def draw(screen, z):
    norm = np.clip((z - MINVAL) / (MAXVAL - MINVAL), 0, 1)
    rgb = interp_color(norm, COLOR0, COLOR1)
    px = rgb.repeat(PIX, 0).repeat(PIX, 1)
    surf = pg.surfarray.make_surface(px)
    screen.blit(surf, (0, 0))

def draw_balls(screen, ballx, bally):
    coords = np.column_stack((ballx, bally)).round().astype(int) * PIX
    for x, y in coords:
        # pg.gfxdraw.filled_circle(screen, x, y, 4, BALLCOLOR)
        pg.draw.circle(screen, BALLCOLOR, (x, y), 4)

def splash(z, v, down, px, py):
    x, y = px // PIX, py // PIX
    v[x, y] += -SPLASH if down else SPLASH

def add_ball(ballx, bally, px, py):
    x, y = px // PIX, py // PIX
    ballx = np.concatenate((ballx, [x]))
    bally = np.concatenate((bally, [y]))
    return ballx, bally

def noise(width, height):
    return np.random.normal(0, .5, (width, height))

def clear(z, v):
    v[:] = 0
    z[:] = noise(*z.shape)
    return np.array([]), np.array([])

def main():
    z = np.zeros((WIDTH, HEIGHT))
    v = np.zeros((WIDTH, HEIGHT))
    ballx, bally = clear(z, v)
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
                    ballx, bally = clear(z, v)
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if evt.button == 2 or mods & pg.KMOD_CTRL:
                    ballx, bally = add_ball(ballx, bally, *evt.pos)
        mouse = pg.mouse.get_pressed()
        if (mouse[0] or mouse[2]) and not mods & pg.KMOD_CTRL:
            splash(z, v, mouse[0], *pg.mouse.get_pos())
        clock.tick(FPS)
        propagate(z, v, WRAP)
        draw(screen, z)
        if ballx.size:
            update_balls(z, ballx, bally)
            draw_balls(screen, ballx, bally)
        pg.display.flip()

if __name__ == '__main__':
    try:
        main()
    finally:
        pg.quit()
