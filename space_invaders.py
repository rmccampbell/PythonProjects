#!/usr/bin/env python3

import os.path as osp
import pygame as pg

WIDTH = 640
HEIGHT = 480

DIR = osp.basename(__file__)
IMAGE_DIR = osp.join(DIR, 'images/space_invaders/')

PLAYER_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'player.png'))
ENEMY_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'enemy.png'))
BULLET_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'bullet.png'))

class Entity:
    def __init__(self, image: pg.Surface, pos: tuple[float, float]):
        self.image = image
        self.x, self.y = pos

    @property
    def rect(self):
        return self.image.get_rect(center=(self.x, self.y))

    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)
    
    def update(self):
        pass

class Player(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(PLAYER_IMAGE, pos)

class Enemy(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(ENEMY_IMAGE, pos)

class Bullet(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(BULLET_IMAGE, pos)

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.player = Player((640/2, 480-30))
        self.enemies = []
        self.bullets = []
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.update()
            self.draw()
            self.events()

    def update(self):
        pass

    def draw(self):
        pg.display.flip()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

def main():
    Game().run()

if __name__ == '__main__':
    main()
