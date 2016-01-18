#!/usr/bin/env python3

import sys, os, pygame, random
from pygame import Color
from pygame.locals import *

HSFILE = os.path.join(os.path.dirname(sys.argv[0]), 'tetris_highscore.txt')

FPS = 60

FRAMECOLOR = (127, 127, 127)
BGCOLOR = (255, 255, 255)

SWIDTH = 280
SHEIGHT = 400
WIDTH = 10
HEIGHT = 20

I = 1
O = 2
T = 3
S = 4
Z = 5
J = 6
L = 7

TYPES = {
    I: dict(
        color = Color('cyan'),
        shape = [[1],
                 [1],
                 [1],
                 [1]],
        blocks = [(0, -2), (0, -1), (0, 0), (0, 1)],
        yoff = 1
    ),
    O: dict(
        color = Color('yellow'),
        shape = [[1, 1],
                 [1, 1]],
        blocks = [(0, 0), (1, 0), (0, 1), (1, 1)],
        yoff = 1
    ),
    T: dict(
        color = Color('purple'),
        shape = [[0, 1, 0],
                 [1, 1, 1]],
        blocks = [(0, -1), (-1, 0), (0, 0), (1, 0)],
        yoff = 0
    ),
    S: dict(
        color = Color('green'),
        shape = [[0, 1, 1],
                 [1, 1, 0]],
        blocks = [(0, -1), (1, -1), (-1, 0), (0, 0)],
        yoff = 0
    ),
    Z: dict(
        color = Color('red'),
        shape = [[1, 1, 0],
                 [0, 1, 1]],
        blocks = [(-1, -1), (0, -1), (0, 0), (1, 0)],
        yoff = 0
    ),
    J: dict(
        color = Color('blue'),
        shape = [[0, 1],
                 [0, 1],
                 [1, 1]],
        blocks = [(0, -1), (0, 0), (-1, 1), (0, 1)],
        yoff = 1
    ),
    L: dict(
        color = Color('orange'),
        shape = [[1, 0],
                 [1, 0],
                 [1, 1]],
        blocks = [(0, -1), (0, 0), (0, 1), (1, 1)],
        yoff = 1
    ),
}

class Shape:
    def __init__(self, type, game):
        self.type = type
        self.game = game
        self.color = TYPES[type]['color']
        self.blocks = TYPES[type]['blocks'][:]
        yoff = TYPES[type]['yoff']
        self.x, self.y = 4, -yoff - 1

    def rotate(self, dir=1):
        for i, (x, y) in enumerate(self.blocks):
            self.blocks[i] = -dir * y, dir * x
        if self.check_collisions():
            self.rotate(-dir)

    def move_down(self):
        self.y += 1
        if self.check_collisions():
            self.y -= 1
            self.lock()

    def move_left(self):
        self.x -= 1
        if self.check_collisions():
            self.x += 1

    def move_right(self):
        self.x += 1
        if self.check_collisions():
            self.x -= 1

    def check_collisions(self):
        for x, y in self.blocks:
            x += self.x
            y += self.y
            if x < 0 or x >= WIDTH:
                return True
            elif y >= HEIGHT:
                return True
            if y >= 0 and game.board[y][x]:
                return True
        return False

    def lock(self):
        for x, y in self.blocks:
            x += self.x
            y += self.y
            if y < 0:
                self.game.gameover()
                return
            self.game.board[y][x] = self.type
        self.game.next_round()

    def draw(self, screen):
        for x, y in self.blocks:
            x += self.x
            y += self.y
            pygame.draw.rect(screen, self.color,
                             ((x + 2) * 20, y * 20, 20, 20))
            pygame.draw.rect(screen, (0, 0, 0),
                             ((x + 2) * 20, y * 20, 20, 20), 1)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SWIDTH, SHEIGHT))
        pygame.display.set_caption('Tetris')
        fonts = pygame.font.get_fonts()
        if 'bauhaus93' in fonts:
            font = 'bauhaus93'
        else:
            font = 'impact'
        self.font = pygame.font.SysFont(font, 28)
        self.font2 = pygame.font.SysFont(font, 34)
        self.font3 = pygame.font.SysFont(font, 56)

    def start(self):
        self.is_over = False
        pygame.key.set_repeat(175, 40)
        self.board = [[0] * WIDTH for i in range(HEIGHT)]
        self.rounds = 0
        self.next_round()

    def run(self):
        self.timer = 0
        self.running = True
        try:
            self.titlescreen()
            clock = pygame.time.Clock()
            while self.running:
                if not self.is_over:
                    self.draw()
                    pygame.display.flip()
                    self.update()
                self.process_events()
                clock.tick(FPS)

        finally:
            pygame.quit()

    def update(self):
        if self.timer >= 50:
            self.timer = 0
            if self.shape:
                self.shape.move_down()

        self.timer += 1

    def next_round(self):
        if self.rounds:
            for y, r in enumerate(self.board):
                if all(r):
                    del self.board[y]
                    self.board.insert(0, [0] * WIDTH)
        self.shape = Shape(random.randrange(1, 8), self)
        self.timer = 0
        #print('Round %d' % self.rounds)
        self.rounds += 1

    def titlescreen(self):
        pygame.key.set_repeat()
        self.is_over = True
        self.screen.fill(FRAMECOLOR)
        self.screen.fill(BGCOLOR, (40, 0, WIDTH * 20, HEIGHT * 20))
        colors = map(Color,
                     ['red', 'orange', 'yellow', 'green', 'cyan', 'purple'])
        letters = [self.font3.render(l, True, c)
                   for l, c in zip('TETRIS', colors)]
        w = sum(i.get_width() for i in letters)
        h = letters[0].get_height()
        x = SWIDTH//2 - w//2
        y = SHEIGHT//2 - h//2 - 20
        for i in letters:
            self.screen.blit(i, (x, y))
            x += i.get_width()
        pygame.display.flip()

    def gameover(self):
        pygame.key.set_repeat()
        self.is_over = True
        try:
            hscore = int(open(HSFILE).read())
        except IOError:
            hscore = 0
        hscore = max(self.rounds, hscore)
        open(HSFILE, 'w').write(str(hscore))

        blur = pygame.Surface((SWIDTH - 80, SHEIGHT))
        blur.fill((255, 255, 255))
        blur.set_alpha(191)
        self.screen.blit(blur, (40, 0))
        colors = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple']
        c1, c2, c3 = map(Color, random.sample(colors, 3))
        msg = self.font2.render('Game Over', True, c1)
        self.screen.blit(msg, ((SWIDTH - msg.get_width()) // 2,
                               (SHEIGHT - msg.get_height()) // 2 - 50))
        scoretxt = self.font.render('Score: %s' % self.rounds, True, c2)
        self.screen.blit(scoretxt,
                         ((SWIDTH - scoretxt.get_width()) // 2,
                          (SHEIGHT - scoretxt.get_height()) // 2 + 0))
        hscoretxt = self.font.render('Highscore: %s' % hscore, True, c3)
        self.screen.blit(hscoretxt,
                         ((SWIDTH - hscoretxt.get_width()) // 2,
                          (SHEIGHT - hscoretxt.get_height()) // 2 + 40))
        pygame.display.flip()

    def draw(self):
        self.screen.fill(FRAMECOLOR)
        self.screen.fill(BGCOLOR, (40, 0, WIDTH * 20, HEIGHT * 20))
        for y, r in enumerate(self.board):
            for x, type in enumerate(r):
                if type:
                    pygame.draw.rect(self.screen, TYPES[type]['color'],
                                     ((x + 2) * 20, y * 20, 20, 20))
                    pygame.draw.rect(self.screen, (0, 0, 0),
                                     ((x + 2) * 20, y * 20, 20, 20), 1)

        if self.shape:
            self.shape.draw(self.screen)

    def process_events(self):
        for e in pygame.event.get():
            if e.type == QUIT:
                self.quit()
            elif e.type == KEYDOWN:
                if (e.key == K_ESCAPE or
                    e.key == K_F4 and e.mod & KMOD_ALT):
                    self.quit()

                elif self.is_over:
                    if e.key in (K_RETURN, K_SPACE):
                        self.start()

                elif self.shape:
                    if e.key == K_LEFT:
                        self.shape.move_left()
                    elif e.key == K_RIGHT:
                        self.shape.move_right()
                    elif e.key == K_DOWN:
                        self.shape.move_down()
                    elif e.key == K_SPACE:
                        self.shape.rotate()

    def quit(self):
        self.running = False



if __name__ == '__main__':
    game = Game()
    game.run()
