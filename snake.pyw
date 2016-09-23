#!/usr/bin/python
import sys, os, pygame, random
from pygame.locals import *


SIZE = 8

DIR = os.path.dirname(sys.argv[0])
HSFILE = os.path.join(DIR, 'snake_highscore.txt')
FONTFILE = os.path.join(DIR, 'bauhaus-93.ttf')

TITLESTR = '''\
####            #        
#               #        
#    #### ####  # ## ####
#### #  #    #  ###  #  #
   # #  # ####  ##   ####
   # #  # #  #  ###  #   
#### #  # ##### # ## ####
'''

TITLE = [[c != ' ' for c in r] for r in TITLESTR.splitlines()]


class Snake:
    color = (255, 0, 0)

    def __init__(self, segments):
        self.segments = list(segments)
        self.maxlen = len(self.segments)
        self.xspeed, self.yspeed = 1, 0
        self.dead = False
        self.has_moved = True

    @property
    def length(self):
        return len(self.segments)

    @property
    def head(self):
        return self.segments[-1]

    def update(self):
        if not self.dead:
            segments = self.segments
            oldx, oldy = self.head
            if self.xspeed or self.yspeed:
                x, y = newhead = oldx + self.xspeed, oldy + self.yspeed
                if newhead in segments or not (0 <= x < 41 and 0 <= y < 41):
                    self.kill()
                else:
                    segments.append(newhead)
                    self.has_moved = True
            if len(segments) > self.maxlen:
                del segments[0]

    def draw(self, screen):
        for segment in self.segments:
            pos = segment[0]*SIZE + SIZE//2, segment[1]*SIZE + SIZE//2
            pygame.draw.circle(screen, self.color, pos, 4)

    def grow(self, amt=1):
        self.maxlen += amt

    def kill(self):
        self.dead = True

    def move_up(self):
        if not self.yspeed and self.has_moved:
            self.xspeed, self.yspeed = 0, -1
            self.has_moved = False

    def move_down(self):
        if not self.yspeed and self.has_moved:
            self.xspeed, self.yspeed = 0, 1
            self.has_moved = False

    def move_left(self):
        if not self.xspeed and self.has_moved:
            self.xspeed, self.yspeed = -1, 0
            self.has_moved = False

    def move_right(self):
        if not self.xspeed and self.has_moved:
            self.xspeed, self.yspeed = 1, 0
            self.has_moved = False


class Game:
    bgcolor = (0, 0, 0)
    foodcolor = (255, 255, 0)

    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Snake')
        self.screen = pygame.display.set_mode((328, 328))
        fonts = pygame.font.get_fonts()
        if os.path.exists(FONTFILE):
            typ, font, s1, s2 = pygame.font.Font, FONTFILE, 32, 24
        elif 'bauhaus93' in fonts:
            typ, font, s1, s2 = pygame.font.SysFont, 'bauhaus93', 32, 24
        else:
            typ, font, s1, s2 = pygame.font.SysFont, 'impact', 42, 32
        self.font1 = typ(font, s1)
        self.font2 = typ(font, s2)
        self.snake = None
        self.is_title = True
        self.is_gameover = False
        self.running = False

    def run(self):
        self.main()

    def start(self):
        self.is_title = False
        self.is_gameover = False
        self.score = 0
        self.highscore = 0
        self.snake = Snake([(18, 20), (19, 20), (20, 20)])
        self.grid = [[0]*41 for i in range(41)]
        self.spawn_food()

    def gameover(self):
        self.is_gameover = True
        try:
            file = open(HSFILE, 'r+')
            highscore = int(file.read())
            file.seek(0)
            file.truncate()
        except IOError:
            file = open(HSFILE, 'w')
            highscore = 0
        self.highscore = max(self.score, highscore)
        file.write(str(self.highscore))

    def main(self):
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            clock.tick(15)
            snake = self.snake
            for e in pygame.event.get():
                if e.type == KEYDOWN:
                    if e.key == K_ESCAPE or e.key == K_F4 and e.mod & KMOD_ALT:
                        self.quit()

                    elif self.is_title or self.is_gameover:
                        if e.key in (K_RETURN, K_SPACE):
                            self.start()

                    else:
                        if e.key == K_UP:
                            snake.move_up()
                        elif e.key == K_DOWN:
                            snake.move_down()
                        elif e.key == K_LEFT:
                            snake.move_left()
                        elif e.key == K_RIGHT:
                            snake.move_right()

                elif e.type == QUIT:
                    self.quit()

            self.update()
            self.draw(self.screen)
            pygame.display.flip()

    def update(self):
        if self.is_title or self.is_gameover:
            return
        snake = self.snake
        snake.update()
        x, y = snake.head
        if self.grid[x][y]:
            self.score += 1
            snake.grow()
            self.grid[x][y]=0
            self.spawn_food()
        if snake.dead:
            self.gameover()

    def spawn_food(self):
        x, y = random.randrange(41), random.randrange(41)
        self.grid[x][y] = 1

    def draw(self, screen):
        screen.fill(self.bgcolor)
        if self.is_title:
            for y, row in enumerate(TITLE):
                for x, cell in enumerate(row):
                    if cell:
                        pos = x*SIZE + SIZE//2 + 8*SIZE, y*SIZE + SIZE//2 + 16*SIZE
                        pygame.draw.circle(screen, Snake.color, pos, 4)
        elif self.is_gameover:
            scoretext = "Score: {}".format(self.score)
            hscoretext = "High Score: {}".format(self.highscore)
            surf1 = self.font1.render('Game Over', True, (0, 0, 255))
            surf2 = self.font2.render(scoretext, True, (0, 0, 255))
            surf3 = self.font2.render(hscoretext, True, (0, 0, 255))
            cx, cy = screen.get_rect().center
            screen.blit(surf1, surf1.get_rect(center=(cx, cy - 50)))
            screen.blit(surf2, surf2.get_rect(center=(cx, cy)))
            screen.blit(surf3, surf3.get_rect(center=(cx, cy + 40)))
        else:
            for x, col in enumerate(self.grid):
                for y, cell in enumerate(col):
                    if cell:
                        pos = x*SIZE + SIZE//2, y*SIZE + SIZE//2
                        pygame.draw.circle(screen, self.foodcolor, pos, 4)
            self.snake.draw(screen)

    def quit(self):
        self.running = False


if __name__ == '__main__':
    try:
        game = Game()
        game.run()
    finally:
        pygame.quit()
