#!/usr/bin/env python3

import os.path as osp
import random
import pygame as pg
from typing import Optional

WIDTH = 1280
HEIGHT = 960
FPS = 60

BGCOLOR = (0, 0, 0)

DIR = osp.basename(__file__)
IMAGE_DIR = osp.join(DIR, 'images/space_invaders/')

# PLAYER_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'player.png'))
# ENEMY_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'enemy.png'))
# BULLET_IMAGE = pg.image.load(osp.join(IMAGE_DIR, 'bullet.png'))

def compute_bbox(points: list[tuple[float, float]]):
    x0 = min(x for x, y in points)
    y0 = min(y for x, y in points)
    x1 = max(x for x, y in points)
    y1 = max(y for x, y in points)
    return pg.Rect(x0, y0, x1-x0, y1-y0)

class Entity:
    def __init__(self, game: 'Game', pos: tuple[float, float],
                 image: Optional[pg.Surface] = None,
                 poly: Optional[list[tuple[float, float]]] = None,
                 color: Optional[tuple[int, int, int]] = None,
                 linewidth=0,
                 bbox: Optional[pg.Rect] = None):
        self.game = game
        self.x, self.y = pos
        self.image = image
        self.poly = poly
        self.color = color
        self.linewidth = linewidth
        if bbox is None:
            if self.image:
                bbox = self.image.get_rect(center=(0, 0))
            elif self.poly:
                bbox = compute_bbox(self.poly)
        self.bbox = pg.Rect(bbox)
        self.alive = True

    @property
    def pos(self):
        return self.x, self.y

    @pos.setter
    def pos(self, pos):
        (self.x, self.y) = pos

    def kill(self):
        self.alive = False

    def get_bbox(self):
        return self.bbox.move(self.pos)

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
    def __init__(self, game, pos: tuple[float, float]):
        poly = [(-40, 40), (40, 40), (0, 0)]
        super().__init__(game, pos, poly=poly, color=(0, 0, 255), linewidth=3)
        self.speed = 10

    def move_left(self):
        self.x -= self.speed
        self.x = max(self.x, 30)

    def move_right(self):
        self.x += self.speed
        self.x = min(self.x, WIDTH-30)

class Enemy(Entity):
    def __init__(self, game, pos: tuple[float, float]):
        poly = [(-40, 20), (0, 10), (40, 20), (20, -20), (0, -10), (-20, -20)]
        super().__init__(game, pos, poly=poly, color=(255, 0, 0), linewidth=3)
        self.speed = 3

    def update(self):
        self.y += self.speed
        if self.get_bbox().bottom > HEIGHT:
            self.game.game_over()

class Bullet(Entity):
    def __init__(self, game, pos: tuple[float, float]):
        poly = [(0, 0), (0, 20)]
        bbox = (-10, 0, 20, 20)
        super().__init__(game, pos, poly=poly, linewidth=5,
                         color=(0, 255, 255), bbox=bbox)
        self.speed = 20

    def update(self):
        self.y -= self.speed
        if self.y < 0:
            self.kill()

    def collide(self, other):
        if isinstance(other, Enemy):
            self.kill()
            other.kill()
            self.game.score += 1

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.font = pg.font.Font(None, 48)
        self.titlefont = pg.font.Font(None, 144)
        self.running = False
        self.player: Player = None
        self.entities: list[Entity] = []
        self.is_game_over = False
        self.enemy_timer = 0
        self.score = 0
        self.start()

    def start(self):
        self.player = Player(self, (WIDTH//2, HEIGHT-80))
        self.entities = [self.player]
        self.is_game_over = False
        self.score = 0
        self.reset_enemy_timer()

    def run(self):
        self.running = True
        clock = pg.time.Clock()
        while self.running:
            self.events()
            self.update()
            self.draw()
            clock.tick(FPS)

    def update(self):
        if self.is_game_over:
            return
        self.collisions()
        for entity in self.entities:
            entity.update()
        self.entities = [e for e in self.entities if e.alive]
        self.enemy_timer -= 1
        if self.enemy_timer <= 0:
            self.spawn(Enemy(self, (random.randrange(60, WIDTH-60), 0)))
            self.reset_enemy_timer()

    def draw(self):
        self.screen.fill(BGCOLOR)
        if self.is_game_over:
            self.draw_game_over()
        else:
            for entity in self.entities:
                entity.draw(self.screen)
            score_img = self.font.render(str(self.score), True, (255, 255, 255))
            self.screen.blit(score_img, (50, 50))
        pg.display.flip()

    def draw_game_over(self):
        img = self.titlefont.render('GAME OVER', True, (0, 0, 255))
        self.screen.blit(img, img.get_rect(center=(WIDTH//2, HEIGHT//2)))

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN:
                if (event.key == pg.K_ESCAPE or
                        event.key == pg.K_F4 and event.mod & pg.KMOD_ALT):
                    self.running = False
                elif self.is_game_over:
                    if event.key in (pg.K_RETURN, pg.K_SPACE):
                        self.start()
                elif event.key == pg.K_SPACE:
                    self.shoot()

        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.player.move_left()
        if keys[pg.K_RIGHT]:
            self.player.move_right()

    def collisions(self):
        for i, e1 in enumerate(self.entities):
            for e2 in self.entities[i+1:]:
                if e1.get_bbox().colliderect(e2.get_bbox()):
                    e1.collide(e2)
                    e2.collide(e1)

    def spawn(self, entity: Entity):
        self.entities.append(entity)

    def reset_enemy_timer(self):
        self.enemy_timer = random.randrange(40, 100)

    def shoot(self):
        self.spawn(Bullet(self, self.player.pos))

    def game_over(self):
        self.is_game_over = True

def main():
    Game().run()

if __name__ == '__main__':
    main()
