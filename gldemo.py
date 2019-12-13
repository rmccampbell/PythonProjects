#!/usr/bin/env python3
import math
import time
import numpy as np
import pygame as pg
import OpenGL
from OpenGL import GL
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays.vbo import VBO
import glm

W, H = 640, 480

VERT_SHADER = b"""
#version 330 core
layout (location = 0) in vec3 aPosition;
layout (location = 1) in vec3 aColor;
out vec3 Color;

uniform mat4 projection;
uniform mat4 modelview;

void main() {
    gl_Position = projection * modelview * vec4(aPosition, 1.0);
    Color = aColor;
}
"""

FRAG_SHADER = b"""
#version 330 core
out vec4 FragColor;
in vec3 Color;

void main() {
    FragColor = vec4(Color, 1.0);
}
"""

Vertex = np.dtype([('position', np.float32, 3),
                   ('color', np.float32, 3)])

def offsetof(dtype, field):
    if isinstance(field, int):
        field = dtype.names[field]
    return dtype.fields[field][1]

vertices = np.array([
    ([-0.5, -0.43, 0.], [1., 0., 0.]),
    ([ 0.5, -0.43, 0.], [0., 1., 0.]),
    ([ 0.0,  0.43, 0.], [0., 0., 1.]),
], dtype=Vertex)

indices = np.array([0, 1, 2], np.uint32)


def main():
    pg.init()
    screen = pg.display.set_mode(
        (W, H), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)

    vertShader = shaders.compileShader(VERT_SHADER, GL_VERTEX_SHADER)
    fragShader = shaders.compileShader(FRAG_SHADER, GL_FRAGMENT_SHADER)
    shader = shaders.compileProgram(vertShader, fragShader)
    glUseProgram(shader)

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vbo = VBO(vertices, GL_STATIC_DRAW)
    ebo = VBO(indices, GL_STATIC_DRAW, GL_ELEMENT_ARRAY_BUFFER)
    with vbo, ebo:
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(0, 3, GL_FLOAT, False, Vertex.itemsize,
                              vbo + offsetof(Vertex, 'position'))
        glVertexAttribPointer(1, 3, GL_FLOAT, False, Vertex.itemsize,
                              vbo + offsetof(Vertex, 'color'))
        glBindVertexArray(0)

    clock = pg.time.Clock()
    while True:
        clock.tick(30)

        glClearColor(.5, .5, .5, 1.)
        glClear(GL_COLOR_BUFFER_BIT)

        x, y, w, h = glGetInteger(GL_VIEWPORT)
        projection = glm.perspective(math.pi/4, w/h, .1, 10)
        glUniformMatrix4fv(glGetUniformLocation(shader, "projection"),
                           1, False, glm.value_ptr(projection))

        view = glm.lookAt(
            glm.vec3(0, 0, 2), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))

        t = pg.time.get_ticks()/1000
        modelview = glm.rotate(view, t*math.pi/2, [0, 1, 0])
        glUniformMatrix4fv(glGetUniformLocation(shader, "modelview"),
                           1, False, glm.value_ptr(modelview))

        glBindVertexArray(vao)
        #glDrawArrays(GL_TRIANGLES, 0, len(vertices))
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, ebo)

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
