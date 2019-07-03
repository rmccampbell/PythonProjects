#!/usr/bin/env python3
import math
import time
import pygame as pg
import OpenGL
from OpenGL import GL, GLU
from OpenGL.GL import *
from OpenGL.GLU import *

W, H = 640, 480

def main():
    pg.init()
    screen = pg.display.set_mode(
        (W, H), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)

    clock = pg.time.Clock()
    while True:
        clock.tick(30)

        glClearColor(.5, .5, .5, 1.)
        glClear(GL_COLOR_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        x, y, w, h = glGetInteger(GL_VIEWPORT)
        gluPerspective(45, w/h, .1, 10)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0., 0., 2., 0., 0., 0., 0., 1., 0.)

        t = pg.time.get_ticks()/1000
        glRotate(t*90%360, 0, 1, 0)

        glBegin(GL_TRIANGLES)
        glColor(1., 0., 0.)
        glVertex(-.5, -.43, 0.)
        glColor(0., 1., 0.)
        glVertex(.5, -.43, 0.)
        glColor(0., 0., 1.)
        glVertex(0, .43, 0.)
        glEnd()

        pg.display.flip()

        if not process_events():
            break

def process_events():
    for e in pg.event.get():
        if e.type == pg.QUIT:
            return False
        elif e.type == pg.KEYDOWN:
            if e.key == pg.K_ESCAPE:
                return False
            if e.key == pg.K_F4 and e.mod & pg.KMOD_ALT:
                return False
        elif e.type == pg.VIDEORESIZE:
            glViewport(0, 0, e.w, e.h)
    return True

if __name__ == '__main__':
    try:
        main()
    finally:
        pg.display.quit()
