#!/usr/bin/env python3

import os.path as osp
import random
import pygame as pg
from typing import Optional

WIDTH = 640
HEIGHT = 480
FPS = 60

BGCOLOR = (0, 0, 0)

DIR = osp.basename(__file__)
IMAGE_DIR = osp.join(DIR, 'images/space_invaders/')

# PLAYER_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'player.png'))
# ENEMY_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'enemy.png'))
# BULLET_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'bullet.png'))

def get_bbox(points: list[tuple[float, float]]):
    x0 = min(x for x, y in points)
    y0 = min(y for x, y in points)
    x1 = max(x for x, y in points)
    y1 = max(y for x, y in points)
    return pg.Rect(x0, y0, x1-x0, y1-y0)

class Entity:
    def __init__(self, pos: tuple[float, float],
                 image: Optional[pg.Surface] = None,
                 poly: Optional[list[tuple[float, float]]] = None,
                 color: Optional[tuple[int, int, int]] = None,
                 linewidth=0,
                 rect: Optional[pg.Rect] = None):
        self.x, self.y = pos
        self.image = image
        self.poly = poly
        self.color = color
        self.linewidth = linewidth
        if rect is None:
            if self.image:
                rect = self.image.get_rect(center=(0, 0))
            elif self.poly:
                rect = get_bbox(self.poly)
        self.rect = pg.Rect(rect)
        self.alive = True

    @property
    def pos(self):
        return self.x, self.y

    @pos.setter
    def pos(self, pos):
        (self.x, self.y) = pos

    def kill(self):
        self.alive = False

    def get_rect(self):
        return self.rect.move(self.pos)

    def draw(self, screen: pg.Surface):
        if self.image:
            img_rect = self.image.get_rect(center=(self.x, self.y))
            screen.blit(self.image, img_rect)
        elif self.poly:
            points = [(x + self.x, y + self.y) for x, y in self.poly]
            pg.draw.polygon(screen, self.color, points, self.linewidth)
        # pg.draw.rect(screen, (255,255,255), self.get_rect(), 1)

    def update(self):
        pass

    def collide(self, other):
        pass

class Player(Entity):
    def __init__(self, pos: tuple[float, float]):
        poly = [(-20, 20), (20, 20), (0, 0)]
        super().__init__(pos, poly=poly, color=(0, 0, 255), linewidth=2)
        self.speed = 5

    def move_left(self):
        self.x -= self.speed
        self.x = max(self.x, 30)

    def move_right(self):
        self.x += self.speed
        self.x = min(self.x, WIDTH-30)

class Enemy(Entity):
    def __init__(self, pos: tuple[float, float]):
        poly = [(-20, 15), (0, 10), (20, 15), (15, 0),
                (20, -15), (0, -10), (-20, -15), (-15, 0)]
        super().__init__(pos, poly=poly, color=(192, 0, 0), linewidth=2)
        self.speed = 1

    def update(self):
        self.y += self.speed

class Bullet(Entity):
    def __init__(self, pos: tuple[float, float]):
        poly = [(0, 0), (0, 10)]
        rect = (-5, 0, 10, 10)
        super().__init__(pos, poly=poly, linewidth=4, color=(255, 0, 0), rect=rect)
        self.speed = 10

    def update(self):
        self.y -= self.speed

    def collide(self, other):
        if isinstance(other, Enemy):
            self.kill()
            other.kill()

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.player = Player((640/2, 480-40))
        self.entities: list[Entity] = [self.player]
        self.running = False
        self.enemy_timer = 0

    def run(self):
        self.running = True
        clock = pg.time.Clock()
        while self.running:
            self.update()
            self.draw()
            self.events()
            clock.tick(FPS)

    def update(self):
        self.collisions()
        for entity in self.entities:
            entity.update()
        self.entities = [e for e in self.entities if e.alive]
        self.enemy_timer += 1
        if self.enemy_timer >= 100:
            self.spawn(Enemy((random.randrange(30, WIDTH-30), 0)))
            self.enemy_timer = 0

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

    def collisions(self):
        for i, e1 in enumerate(self.entities):
            for e2 in self.entities[i+1:]:
                if e1.get_rect().colliderect(e2.get_rect()):
                    e1.collide(e2)
                    e2.collide(e1)

    def spawn(self, entity: Entity):
        self.entities.append(entity)

    def shoot(self):
        self.spawn(Bullet(self.player.pos))

def main():
    Game().run()

if __name__ == '__main__':
    main()
