#!/usr/bin/python3
import pygame, math #, pygame.gfxdraw
from pygame.locals import *

SPEED = math.pi/200
COLOR = (255, 255, 255)
BGCOLOR = (0, 0, 0)
PIXSIZE = 2

WIDTH, HEIGHT = 400, 400
SW, SH = 20, 20

DEG = math.pi/180

def pixelize(point):
    x, y = point
    px = int(WIDTH//2 + x*WIDTH//SW)
    py = int(HEIGHT//2 - y*HEIGHT//SH)
    return px, py

def pixel_r(r):
    return int(r * WIDTH//SW)

def rotate_x(point, angle):
    x, y, z = point
    return (x,
            y*math.cos(angle) - z*math.sin(angle),
            y*math.sin(angle) + z*math.cos(angle))

def rotate_y(point, angle):
    x, y, z = point
    return (x*math.cos(angle) + z*math.sin(angle),
            y,
            -x*math.sin(angle) + z*math.cos(angle))

def rotate_z(point, angle):
    x, y, z = point
    return (x*math.cos(angle) - y*math.sin(angle),
            x*math.sin(angle) + y*math.cos(angle),
            z)

def poly(points):
    return list(points) + [points[0]]

def cube(pos, dims):
    x,y,z = pos
    l,w,h = dims
    return [(x,y,z), (x+l,y,z), (x+l,y+w,z), (x,y+w,z), (x,y,z), (x,y,z+h),
            (x+l,y,z+h), (x+l,y+w,z+h), (x,y+w,z+h), (x,y,z+h), (x+l,y,z+h),
            (x+l,y,z), (x+l,y+w,z), (x+l,y+w,z+h), (x,y+w,z+h), (x,y+w,z)]

def cube2(pos, dims):
    x,y,z = pos
    l,w,h = dims
    return ([(x,y,z), (x+l,y,z), (x+l,y+w,z), (x,y+w,z), (x,y,z), (x,y,z+h)],
	    [(x+l,y+w,z+h), (x,y+w,z+h), (x,y,z+h), (x+l,y,z+h),
	     (x+l,y+w,z+h), (x+l,y+w,z)], [(x+l,y,z), (x+l,y,z+h)],
	    [(x,y+w,z+h),(x,y+w,z)])

def circle(pos, r, axis):
    x,y,z = pos
    if axis == 0:
        points = [(x, y+r*math.cos(math.pi*th/20), z+r*math.sin(math.pi*th/20))
                  for th in range(40)]
    elif axis == 1:
        points = [(x+r*math.cos(math.pi*th/20), y, z+r*math.sin(math.pi*th/20))
                  for th in range(40)]
    elif axis == 2:
        points = [(x+r*math.cos(math.pi*th/20), y+r*math.sin(math.pi*th/20), z)
                  for th in range(40)]
    return poly(points)

def translate(poly, r):
    return [(x + r[0], y + r[1], z + r[2]) for x, y, z in poly]

def rotate(poly, axis, angle):
    if axis == 0:
        return [rotate_x(p, angle) for p in poly]
    elif axis == 1:
        return [rotate_y(p, angle) for p in poly]
    elif axis == 2:
        return [rotate_z(p, angle) for p in poly]



points = [
    (0, 0, 10),
    (0, 5, 0),
    (4, 7, 0),
    (6, 8, 4),
    (1, 4, -6),
    (9, 3, -10),
    (3, -2, 0),
    (1, -9, -7),
    (4, 5, 5),
    (-5, -3, -9),
    (2, 9, -7),
    (-1, -9, -6),
    (5, -3, -6),
    (-6, -6, 2),
    (6, 7, 6),
    (-9, 0, -1),
    (-9, -7, -7),
    (0, -10, 10),
    (6, 6, -9),
    (-6, 7, -3),
    (-2, 3, -5),
    (3, -9, 3),
    (-1, 3, 9),
    (8, 9, 4),
    (4, -2, 5),
    (-5, 10, 9),
    (4, 10, 6),
    (-5, -4, 1),
    (1, -3, -4),
    (-8, 9, 8),
    (-9, -10, 7),
    (6, 2, -8),
]

polys = [
    [(0, 3, 3), (9, 4, 2)],
    [(3, 2, -6), (-1, 4, -7), (-3, 7, -8), (-7, 2, -7)],
    poly([(3, -2, -4), (4, 5, -6), (7, 9, -8)]),
    poly([(-1, -2, -7), (-5, -9, -2), (-8, -1, 1), (-2, -4, 6)]),
    poly([(-5, 8, 5), (-7, 4, 7), (-5, 0, 5), (-2, 1.5, 2), (-2, 6.5, 2)]),
    cube((-4, 0, -7), (5, 5, 5)),
    circle((6, 2, -1), 2, 0),
    circle((5, -7, 3), 3, 0),
    circle((5, -7, 3), 3, 1),
##    circle((5, -7, 3), 3, 2),
    translate(rotate(cube((-2, -2, -2), (4, 4, 4)), 2, 45*DEG), (4, 4, 4))
]

spheres = [
    ((5, -7, 3), 3),
]



def rotate_right():
    global yrspeed, holding_right
    holding_right = True
    yrspeed = SPEED
def rotate_left():
    global yrspeed, holding_left
    holding_left = True
    yrspeed = -SPEED
def rotate_down():
    global xrspeed, holding_down
    holding_down = True
    xrspeed = SPEED
def rotate_up():
    global xrspeed, holding_up
    holding_up = True
    xrspeed = -SPEED

def stop_right():
    global yrspeed, holding_right
    holding_right = False
    if holding_left:
        rotate_left()
    else:
        yrspeed = 0
def stop_left():
    global yrspeed, holding_left
    holding_left = False
    if holding_right:
        rotate_right()
    else:
        yrspeed = 0
def stop_down():
    global xrspeed, holding_down
    holding_down = False
    if holding_up:
        rotate_up()
    else:
        xrspeed = 0
def stop_up():
    global xrspeed, holding_up
    holding_up = False
    if holding_down:
        rotate_down()
    else:
        xrspeed = 0


def main(points=points, polys=polys, spheres=spheres):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    global holding_right, holding_left, holding_down, holding_up
    global yrspeed, xrspeed
    holding_left, holding_right, holding_up, holding_down = (False,)*4
    yrot, xrot = 0, 0
    yrspeed, xrspeed = 0, 0

    points, polys, spheres = points[:], polys[:], spheres[:]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_RIGHT:
                    rotate_right()
                elif event.key == K_LEFT:
                    rotate_left()
                elif event.key == K_DOWN:
                    rotate_down()
                elif event.key == K_UP:
                    rotate_up()

                elif event.key == K_ESCAPE:
                    running = False
                elif event.key == K_F4 and event.mod & KMOD_ALT:
                    running = False

            if event.type == KEYUP:
                if event.key == K_RIGHT:
                    stop_right()
                elif event.key == K_LEFT:
                    stop_left()
                elif event.key == K_DOWN:
                    stop_down()
                elif event.key == K_UP:
                    stop_up()

            elif event.type == QUIT:
                running = False

        screen.fill(BGCOLOR)

        for i, p in enumerate(points):
            p = rotate_y(p, yrspeed)
            points[i] = p = rotate_x(p, xrspeed)

            pixp = pixelize(p[:2])
##            pixx = int(200 + p[0]*20)
##            pixy = int(200 - p[1]*20)

            pygame.draw.circle(screen, COLOR, pixp, PIXSIZE)
            #pygame.gfxdraw.filled_circle(screen, pixx, pixy, pixsize, COLOR)

        for poly in polys:
            pixs = []
            for i, p in enumerate(poly):
                p = rotate_y(p, yrspeed)
                poly[i] = p = rotate_x(p, xrspeed)

                pixp = pixelize(p[:2])
##                pixx = int(200 + p[0]*20)
##                pixy = int(200 - p[1]*20)
                pixs.append(pixp)

            pygame.draw.lines(screen, COLOR, False, pixs, 1)

        for i, (p, r) in enumerate(spheres):
            p = rotate_y(p, yrspeed)
            p = rotate_x(p, xrspeed)
            spheres[i] = (p, r)

            pixp = pixelize(p[:2])
            pixr = pixel_r(r)
##            pixx = int(200 + p[0]*20)
##            pixy = int(200 - p[1]*20)
##            pixr = int(r * 20)

            pygame.draw.circle(screen, COLOR, pixp, pixr, 1)

        pygame.display.flip()
        pygame.time.wait(10)

if __name__ == '__main__':
    try:
        main()
    finally:
        pygame.display.quit()
