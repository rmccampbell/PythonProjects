#!/usr/bin/python

import sys, os, pygame, random
from pygame import Color
from pygame.locals import *

DIR = os.path.dirname(sys.argv[0])
HSFILE = os.path.join(DIR, 'tetris_highscore.txt')
FONTFILE = os.path.join(DIR, 'bauhaus-93.ttf')

FPS = 60

FRAMECOLOR = (127, 127, 127)
BGCOLOR = (255, 255, 255)

SWIDTH = 280
SHEIGHT = 400
WIDTH = 10
HEIGHT = 20

TYPES = [
    None,
    dict( # I
        color = Color('cyan'),
        blocks = [(0, -2), (0, -1), (0, 0), (0, 1)],
        yoff = 1
    ),
    dict( # O
        color = Color('yellow'),
        blocks = [(0, 0), (1, 0), (0, 1), (1, 1)],
        yoff = 1
    ),
    dict( # T
        color = Color('purple'),
        blocks = [(0, -1), (-1, 0), (0, 0), (1, 0)],
        yoff = 0
    ),
    dict( # S
        color = Color('green'),
        blocks = [(0, -1), (1, -1), (-1, 0), (0, 0)],
        yoff = 0
    ),
    dict( # Z
        color = Color('red'),
        blocks = [(-1, -1), (0, -1), (0, 0), (1, 0)],
        yoff = 0
    ),
    dict( # J
        color = Color('blue'),
        blocks = [(0, -1), (0, 0), (-1, 1), (0, 1)],
        yoff = 1
    ),
    dict( # L
        color = Color('orange'),
        blocks = [(0, -1), (0, 0), (0, 1), (1, 1)],
        yoff = 1
    ),
]

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

    def move_left(self):
        self.x -= 1
        if self.check_collisions():
            self.x += 1

    def move_right(self):
        self.x += 1
        if self.check_collisions():
            self.x -= 1

    def move_down(self):
        self.y += 1
        if self.check_collisions():
            self.y -= 1
            self.lock()

    def drop(self):
        self.y += 1
        while not self.check_collisions():
            self.y += 1
        self.y -= 1
        self.lock()

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
        pygame.display.set_caption('Tetris')
        self.screen = pygame.display.set_mode((SWIDTH, SHEIGHT))
        fonts = pygame.font.get_fonts()
        if os.path.exists(FONTFILE):
            typ, font, s1, s2, s3 = pygame.font.Font, FONTFILE, 28, 34, 56
        elif 'bauhaus93' in fonts:
            typ, font, s1, s2, s3 = pygame.font.SysFont, 'bauhaus93', 28, 34, 56
        else:
            typ, font, s1, s2, s3 = pygame.font.SysFont, 'impact', 36, 44, 72
        self.font = typ(font, s1)
        self.font2 = typ(font, s2)
        self.font3 = typ(font, s3)

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

        fade = pygame.Surface((SWIDTH - 80, SHEIGHT))
        fade.fill((255, 255, 255))
        fade.set_alpha(210)
        self.screen.blit(fade, (40, 0))

        colors = ['red', 'orange', 'green', 'blue', 'purple']
        c1, c2, c3 = map(Color, random.sample(colors, 3))
        msg = self.font2.render('Game Over', True, c1)
        self.screen.blit(msg, ((SWIDTH - msg.get_width()) // 2,
                               (SHEIGHT - msg.get_height()) // 2 - 50))
        scoretxt = self.font.render('Score: %s' % self.rounds, True, c2)
        self.screen.blit(scoretxt,
                         ((SWIDTH - scoretxt.get_width()) // 2,
                          (SHEIGHT - scoretxt.get_height()) // 2))
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
                    elif e.key == K_UP:
                        self.shape.rotate()
                    elif e.key == K_SPACE:
                        self.shape.drop()

    def quit(self):
        self.running = False



if __name__ == '__main__':
    game = Game()
    game.run()
