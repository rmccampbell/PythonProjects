#!/usr/bin/env python
import sys
import os
import argparse
import pygame
import socket
import select
import time
from pygame.locals import *

HOST = 'localhost'
PORT = 9999

W = 500
H = 400

def serve(port=PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.setblocking(False)
    sock.bind(('', port))
    print('listening on port %d...' % port)
    try:
        while True:
            rlist, wlist, xlist = select.select([sock], [], [], 1)
            if rlist:
                data, addr = sock.recvfrom(256)
                if data == b'connect':
                    sock.sendto(b'connected', addr)
                    break
    except KeyboardInterrupt:
        return
    print('connected to %s on port %d' % addr)
    main(sock, addr, True)

def connect(host=HOST, port=PORT):
    host = socket.gethostbyname(host)
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.setblocking(False)
    print('connecting to %s on port %d...' % addr)
    try:
        while True:
            sock.sendto(b'connect', addr)
            rlist, wlist, xlist = select.select([sock], [], [], 1)
            if rlist:
                try:
                    data, addr2 = sock.recvfrom(256)
                except ConnectionResetError:
                    time.sleep(1)
                    continue
                if addr2 == addr and data == b'connected':
                    break
    except KeyboardInterrupt:
        return
    print('connected')
    main(sock, addr, False)

def main(sock, addr, server=False):
    x = W//2 - 100
    y = H//2
    x2 = W//2 + 100
    y2 = H//2
    dx, dy = 0, 0
    color = (0, 0, 255)
    color2 = (255, 0, 0)
    if server:
        os.environ['SDL_VIDEO_WINDOW_POS'] = '120, 140'
        title = 'Server'
    else:
        os.environ['SDL_VIDEO_WINDOW_POS'] = '720, 140'
        x, y, x2, y2 = x2, y2, x, y
        color, color2 = color2, color
        title = 'Client'

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()
    running = True

    while running:
        rlist, wlist, xlist = select.select([sock], [], [], 0)
        if rlist:
            data, addr2 = sock.recvfrom(256)
            if addr2 == addr:
                if data == b'close':
                    running = False
                else:
                    try:
                        x2, y2 = map(int, data.split(b','))
                    except ValueError as e:
                        print('ValueError: %s; data=%r' % (e, data))
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    dy = -5
                elif event.key == K_DOWN:
                    dy = 5
                elif event.key == K_LEFT:
                    dx = -5
                elif event.key == K_RIGHT:
                    dx = 5
                elif (event.key == K_ESCAPE or
                      event.key == K_F4 and event.mod & KMOD_ALT):
                    running = False
            elif event.type == KEYUP:
                if event.key in (K_UP, K_DOWN):
                    dy = 0
                elif event.key in (K_LEFT, K_RIGHT):
                    dx = 0
        x += dx
        y += dy
        if dx or dy:
            sock.sendto(('%+04d,%+04d' % (x, y)).encode('ascii'), addr)
        screen.fill((255, 255, 255))
        pygame.draw.circle(screen, color2, (x2, y2), 10)
        pygame.draw.circle(screen, color, (x, y), 10)
        pygame.display.flip()
        clock.tick(20)

    sock.sendto(b'close', addr)
    sock.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('host', nargs='?', default=HOST,
                   help='default: %(default)s')
    p.add_argument('-p', '--port', type=int, default=PORT,
                   help='default: %(default)s')
    p.add_argument('-s', '--server', action='store_true')
    args = p.parse_args()
    if args.server:
        serve(args.port)
    else:
        connect(args.host, args.port)
