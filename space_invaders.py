#!/usr/bin/env python3

import os.path as osp
import pygame as pg
from typing import Optional

WIDTH = 640
HEIGHT = 480

BGCOLOR = (0, 0, 0)

DIR = osp.basename(__file__)
IMAGE_DIR = osp.join(DIR, 'images/space_invaders/')

# PLAYER_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'player.png'))
# ENEMY_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'enemy.png'))
# BULLET_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'bullet.png'))

class Entity:
    def __init__(self, pos: tuple[int, int],
                 image: Optional[pg.Surface] = None,
                 poly: Optional[list[tuple[int, int]]] = None,
                 color: Optional[tuple[int, int, int]] = None,
                 linewidth=0):
        self.x, self.y = pos
        self.image = image
        self.poly = poly
        self.color = color
        self.linewidth = linewidth

    @property
    def pos(self):
        return self.x, self.y

    @pos.setter
    def pos(self, pos):
        (self.x, self.y) = pos

    def get_rect(self):
        return self.image.get_rect(center=(self.x, self.y))

    def get_poly(self):
        return [(x + self.x, y + self.y) for x, y in self.poly]

    def draw(self, screen: pg.Surface):
        if self.image:
            screen.blit(self.image, self.get_rect())
        elif self.poly:
            pg.draw.polygon(screen, self.color, self.get_poly(), self.linewidth)

    def update(self):
        pass

class Player(Entity):
    def __init__(self, pos: tuple[int, int]):
        poly = [(-20, 20), (20, 20), (0, 0)]
        super().__init__(pos, poly=poly, color=(0, 0, 255), linewidth=2)
        self.speed = 1

    def move_left(self):
        self.x -= self.speed
        self.x = max(self.x, 30)

    def move_right(self):
        self.x += self.speed
        self.x = min(self.x, WIDTH-30)

class Enemy(Entity):
    def __init__(self, pos: tuple[int, int]):
        super().__init__(pos)

class Bullet(Entity):
    def __init__(self, pos: tuple[int, int]):
        super().__init__(pos, poly=[(0, 0), (0, 10)], linewidth=4, color=(255, 0, 0))
        self.speed = 1

    def update(self):
        self.y -= self.speed

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.player = Player((640/2, 480-40))
        self.entities: list[Entity] = [self.player]
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.update()
            self.draw()
            self.events()

    def update(self):
        for entity in self.entities:
            entity.update()

    def draw(self):
        self.screen.fill(BGCOLOR)
        for entity in self.entities:
            entity.draw(self.screen)
        pg.display.flip()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN:
                if (event.key == pg.K_ESCAPE or
                        event.key == pg.K_F4 and event.mod & pg.KMOD_ALT):
                    self.running = False
                if event.key == pg.K_SPACE:
                    self.shoot()

        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.player.move_left()
        if keys[pg.K_RIGHT]:
            self.player.move_right()

    def spawn(self, entity: Entity):
        self.entities.append(entity)

    def shoot(self):
        self.spawn(Bullet(self.player.pos))

def main():
    Game().run()

if __name__ == '__main__':
    main()
