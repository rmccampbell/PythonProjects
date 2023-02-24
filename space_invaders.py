#!/usr/bin/env python3

import os.path as osp
import pygame as pg

WIDTH = 640
HEIGHT = 480

DIR = osp.basename(__file__)
IMAGE_DIR = osp.join(DIR, 'images/space_invaders/')

# PLAYER_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'player.png'))
# ENEMY_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'enemy.png'))
# BULLET_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'bullet.png'))

class Entity:
    def __init__(self, pos: tuple[float, float], image=None, poly=None,
                 color=None, linewidth=0):
        self.x, self.y = pos
        self.image = image
        self.poly = poly
        self.color = color
        self.linewidth = linewidth

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
    def __init__(self, pos: tuple[float, float]):
        super().__init__(pos)

class Enemy(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(pos)

class Bullet(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(pos)

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.player = Player((640/2, 480-30))
        self.entities = [self.player]
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
        for entity in self.entities:
            entity.draw(self.screen)
        pg.display.flip()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

def main():
    Game().run()

if __name__ == '__main__':
    main()
