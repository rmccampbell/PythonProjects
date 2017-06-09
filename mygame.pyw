#!/usr/bin/env python3

import pygame, sys, os, math, random
from pygame.locals import *


## CONSTANTS
FRAMERATE = 20
SCREENSIZE = (640, 480)
BGCOLOR = pygame.Color(223, 255, 223)

RIGHT = 0
DOWN = 1
LEFT = 2
UP = 3

X, Y = 0, 1


## DIRECTION HELPER FUNCTIONS
def axisof(direct):
    """Calculate axis of direction"""
    return direct % 2
def signof(direct):
    """Calculate sign of direction"""
    return (-1)**(direct // 2)
def rotated(direct, amt):
    """Calculate direction rotated clockwise by 90 degree increments"""
    return (direct + amt) % 4
def xcomp(direct):
    """Calculate x component of direction"""
    return (direct + 1) % 2 * signof(direct)
def ycomp(direct):
    """Calculate y component of direction"""
    return direct % 2 * signof(direct)
def oppaxis(axis):
    """Calculate opposite of given axis"""
    return (axis + 1) % 2



## UTILITY FUNCTIONS
def load_image(name, colorkey = (255, 0, 255)):
    base = os.path.dirname(__file__)
    fullname = os.path.join(base, 'images', name + '.png')
    image = pygame.image.load(fullname)
    if colorkey:
        image.set_colorkey(colorkey)
        return image.convert()
    else:
        return image.convert_alpha()



## CORE CLASSES
class Animation(list):
    def __init__(self, image, length = 1, offset = (0,0), speed = 1):
        self.name = None
        if not isinstance(image, pygame.Surface):
            self.name = image
            image = load_image(image)
        self.image = image
        self.offset = offset
        self.speed = speed
        self.width = width = image.get_width() / length
        self.height = height = image.get_height()

        for i in range(length):
            self.append(image.subsurface(i * width, 0, width, height))

    def get_rect(self, pos = (0, 0)):
        x, y = pos
        offsetx, offsety = self.offset
        return pygame.Rect(x - offsetx, y - offsety,
                           self.width, self.height)

    def __repr__(self):
        return 'Animation({!r}, {}, {}, {})'.format(
            self.name, len(self), self.offset, self.speed)



## GAME CLASSES
class Character(pygame.sprite.Sprite):
    BASESPEED = 0
    ANIMS = {}

    @classmethod
    def load(cls):
        pass

    def __init__(self, pos, game=None, *groups):
        super().__init__(*groups)
        self.game = game
        self.pos = list(pos)
        self.speed = [0, 0]
        self.walking = [False] * 4
        self.dir = DOWN
        self.frame = 0
        self.anim = None
        self.playing_once = False
        self.move_locked = 0
        self.action_locked = 0
        self.dir_locked = 0
        self.boundrect = self.BOUNDRECT.move(pos)

    def update(self):
        if self.move_locked:
            self.move_locked -= 1
##            if self.move_locked == 0:
##                self.resume_walk()
        else:
            self.move()
        if self.action_locked:
            self.action_locked -= 1
        if self.dir_locked:
            self.dir_locked -= 1

        self.image = self.anim[int(self.frame)]
        self.rect = self.anim.get_rect(self.pos)
        self.boundrect = self.BOUNDRECT.move(self.pos)
        self.frame += self.anim.speed
        if self.frame >= len(self.anim):
            self.frame = 0
            if self.playing_once:
                self.resume_anim()

    def move(self):
        if not self.test_future_collisions(X):
            self.pos[X] += self.speed[X]
        if not self.test_future_collisions(Y):
            self.pos[Y] += self.speed[Y]

    def take_damage(self):
        self.set_anim(self.ANIMS['die'])
        self.action_locked = 26
        print(self, 'damaged')

    def test_collision_with(self, other, offset=(0, 0)):
        rect = self.boundrect.move(*offset)
        return rect.colliderect(other.boundrect)

    def test_wall_collision(self, offset=(0, 0)):
        rect = self.boundrect.move(*offset)
        return not self.game.walls.contains(rect)

    def test_collisions(self, offset=(0, 0)):
        if self.test_wall_collision(offset):
            return True
        for sprite in self.game.allsprites:
            if sprite is self: continue
            if self.test_collision_with(sprite, offset):
                #print("{}: {} collision with: {}".format(self, 'XY'[axis], sprite))
                return True
        return False

    def test_future_collisions(self, axis=None):
        offset = list(self.speed)
        if axis != None:
            offset[oppaxis(axis)] = 0
        return self.test_collisions(offset)

    def set_anim(self, anim, frame=None):
        #print(self.anim, anim)
        if self.playing_once:
            return
        if frame is None:
            if self.anim == anim:
                frame = self.frame
            else:
                frame = 0
        self.anim = anim
        self.frame = frame

    def play_anim_once(self, anim, frame=0):
        self.playing_once = True
        self.anim = anim
        self.frame = frame

    def resume_anim(self):
        self.playing_once = False
        if self.is_walking():
            self.set_anim(self.ANIMS['walk'][self.dir])
        else:
            self.set_anim(self.ANIMS['stand'][self.dir])

    @property
    def x(self):
        return self.pos[X]
    @property
    def y(self):
        return self.pos[Y]
    @x.setter
    def x(self, value):
        self.pos[X] = value
    @y.setter
    def y(self, value):
        self.pos[Y] = value

    @property
    def xspeed(self):
        return self.speed[X]
    @property
    def yspeed(self):
        return self.speed[Y]
    @xspeed.setter
    def xspeed(self, value):
        self.speed[X] = value
    @yspeed.setter
    def yspeed(self, value):
        self.speed[Y] = value

    def is_walking_x(self):
        return self.walking[RIGHT] or self.walking[LEFT]
    def is_walking_y(self):
        return self.walking[DOWN] or self.walking[UP]
    def is_walking(self):
        return any(self.walking)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.pos)


class Player(Character):
    BASESPEED = 4
    SWORDRANGE = 24
    BOUNDRECT = Rect(-8, -8, 16, 16)

    @classmethod
    def load(cls):
        cls.ANIMS = dict(
            #[RIGHT, DOWN, LEFT, UP]
            stand = [
                Animation('linkright', 1, (16, 24)),
                Animation('linkfront', 1, (16, 24)),
                Animation('linkleft', 1, (16, 24)),
                Animation('linkback', 1, (16, 24)),
            ],
            walk = [
                Animation('linkwalkingright', 10, (16, 24)),
                Animation('linkwalkingfront', 10, (16, 24)),
                Animation('linkwalkingleft', 10, (16, 24)),
                Animation('linkwalkingback', 10, (16, 24)),
            ],
            attack = [
                Animation('linkswordright', 9, (21, 35)),
                Animation('linkswordfront', 9, (24, 40)),
                Animation('linkswordleft', 9, (21, 35)),
                Animation('linkswordback', 9, (24, 24)),
            ],
        )

    def __init__(self, pos, game=None, *groups):
        super().__init__(pos, game, *groups)
        self.anim = self.ANIMS['stand'][DOWN]
        self.image = self.anim[0]
        self.rect = self.anim.get_rect(pos)
        self.holding_key = [False] * 4
        self.dir_stack = []

    def update(self):
        self.handle_walking()
        super().update()

    def handle_walking(self):
        if not self.move_locked:
            self.speed = [0, 0]
            self.walking = [None] * 4
            xdir, ydir = None, None
            for dir in self.dir_stack:
                if axisof(dir) == X:
                    xdir = dir
                else:
                    ydir = dir
            if xdir != None:
                self.speed[X] = signof(xdir) * self.BASESPEED
                self.walking[xdir] = True
            if ydir != None:
                self.speed[Y] = signof(ydir) * self.BASESPEED
                self.walking[ydir] = True
            if self.dir_stack:
                if not self.dir_locked:
                    self.dir = self.dir_stack[-1]
                self.set_anim(self.ANIMS['walk'][self.dir])
            else:
                self.set_anim(self.ANIMS['stand'][self.dir])

    def walk(self, direct):
        self.dir_stack.append(direct)

    def stop(self, direct):
        self.dir_stack.remove(direct)

##    def walk(self, direct):
##        self.holding_key[direct] = True
##        if self.move_locked:
##            return
##        self.dir = direct
##        self.walking[direct] = True
##
##        opp_dir = rotated(direct, 2)
##        self.walking[opp_dir] = False
##
##        axis, sign = axisof(direct), signof(direct)
##        self.speed[axis] = sign * self.BASESPEED
##
##        self.set_anim(self.ANIMS['walk'][direct])
##
##    def resume_walk(self):
##        if self.holding_key[self.dir]:
##            self.stop(self.dir)
##            self.walk(self.dir)
##        else:
##            self.stop(self.dir)
##
##    def stop(self, direct):
##        self.walking[direct] = False
##        self.holding_key[direct] = False
##
##        opp_dir = rotated(direct, 2)
##        if self.holding_key[opp_dir]:
##            self.walk(opp_dir)
##
##        else:
##            axis = axisof(direct)
##            self.speed[axis] = 0
##
##            dir_1 = rotated(direct, 1)
##            dir_2 = rotated(direct, -1)
##            if self.walking[dir_1]:
##                if not self.dir == dir_1:
##                    self.walk(dir_1)
##            elif self.walking[dir_2]:
##                if not self.dir == dir_2:
##                    self.walk(dir_2)
##
##            else:
##                self.set_anim(self.ANIMS['stand'][direct])

    def get_swordrect(self):
        x, y = self.pos
        r = self.SWORDRANGE
        if self.dir == RIGHT:
            return Rect(x, y-r, r, 2*r)
        elif self.dir == DOWN:
            return Rect(x-r, y, 2*r, r)
        if self.dir == LEFT:
            return Rect(x-r, y-r, r, 2*r)
        elif self.dir == UP:
            return Rect(x-r, y-r, 2*r, r)

    def attack(self):
        if not self.action_locked:
            self.move_locked = 9
            self.action_locked = 9
            self.play_anim_once(self.ANIMS['attack'][self.dir])
            self.hit_targets()

    def hit_targets(self):
        swordrect = self.get_swordrect()
        for sprite in self.game.allsprites:
            if sprite is self: continue
            if swordrect.colliderect(sprite.boundrect):
                print('Hit', sprite)
                sprite.take_damage()


class NPC(Character):
    def __init__(self, pos, game=None, *groups):
        super().__init__(pos, game, *groups)

    @classmethod
    def spawn(cls, area=None, game=None, *groups):
        if area is None:
            area = game.screen.get_rect()
        step = cls.BASESPEED
        while True:
            char = cls((random.randrange(area.x, area.right, step),
                        random.randrange(area.y, area.bottom, step)),
                       game, *groups)
            if char.test_collisions():
                char.remove(*groups)
            else:
                return char

    @classmethod
    def spawn_n(cls, num, area=None, game=None, *groups):
        if area is None:
            area = game.screen.get_rect()
        return [cls.spawn(area, game, *groups) for i in range(num)]


class Enemy(NPC):
    def __init__(self, pos, game=None, *groups):
        super().__init__(pos, game, *groups)
        self.steps = 0
        self.dir = DOWN

    def update(self):
        if self.steps <= 0 and not self.action_locked:
            self.change_dir()
        self.steps -= 1
        super().update()

    def change_dir(self):
        self.dir = direct = random.randrange(4)
        self.steps = random.randint(5, 40)
        axis, sign = axisof(direct), signof(direct)
        self.speed[axis] = sign * self.BASESPEED
        self.speed[oppaxis(axis)] = 0
        self.set_anim(self.ANIMS['walk'][direct])

    def attack(self, other):
        pass


class Octorok(Enemy):
    BASESPEED = 2
    BOUNDRECT = Rect(-8, -8, 16, 16)

    @classmethod
    def load(cls):
        cls.ANIMS = dict(
            #[RIGHT, DOWN, LEFT, UP]
            stand = [
                Animation('octorokright', 2, (8, 8), .25),
                Animation('octorokfront', 2, (8, 8), .25),
                Animation('octorokleft', 2, (8, 8), .25),
                Animation('octorokback', 2, (8, 8), .25),
            ],
            walk = [
                Animation('octorokright', 2, (8, 8), .25),
                Animation('octorokfront', 2, (8, 8), .25),
                Animation('octorokleft', 2, (8, 8), .25),
                Animation('octorokback', 2, (8, 8), .25),
            ],
            attack = [
                Animation('octorokrightshoot', 2, (12, 8), .25),
                Animation('octorokfrontshoot', 2, (8, 8), .25),
                Animation('octorokleftshoot', 2, (12, 8), .25),
                Animation('octorokbackshoot', 2, (8, 8), .25),
            ],
            die = Animation('octorokdie', 13, (16, 16), .5)
        )

    def __init__(self, pos, *groups):
        super().__init__(pos, *groups)
        self.anim = self.ANIMS['stand'][DOWN]
        self.image = self.anim[0]
        self.rect = self.anim.get_rect(pos)




## GAME CONTROLLER
class Game:
    def quit(self):
        self.running = False

    def draw_background(self, surf, rect=None):
        surf.fill(BGCOLOR, rect)

    def init(self):
        #Move window out of the way
        os.environ['SDL_VIDEO_WINDOW_POS'] = '720, 140'

        pygame.init()
        screen = self.screen = pygame.display.set_mode(SCREENSIZE)

        self.draw_background(screen)
        pygame.display.flip()

        Player.load()
        Octorok.load()

    ### GAME START ###
    def main(self):
        self.init()
        screen = self.screen

        self.walls = pygame.Rect((0, 0), SCREENSIZE)
        allsprites = self.allsprites = pygame.sprite.OrderedUpdates()
        player = Player((48, 48), self, allsprites)
        Octorok.spawn_n(random.randint(5,15), None, self, allsprites)

        clock = pygame.time.Clock()
        self.running = True

        ## GAME LOOP
        while self.running:
            clock.tick(FRAMERATE)

            for e in pygame.event.get():
                if e.type == KEYDOWN:
                    if e.key == K_UP:
                        player.walk(UP)
                    elif e.key == K_DOWN:
                        player.walk(DOWN)
                    elif e.key == K_LEFT:
                        player.walk(LEFT)
                    elif e.key == K_RIGHT:
                        player.walk(RIGHT)
                    elif e.key == K_SPACE:
                        player.attack()

                    elif e.key == K_ESCAPE or \
                         e.key == K_F4 and e.mod & KMOD_ALT:
                        self.quit()

                elif e.type == KEYUP:
                    if e.key == K_UP:
                        player.stop(UP)
                    elif e.key == K_DOWN:
                        player.stop(DOWN)
                    elif e.key == K_LEFT:
                        player.stop(LEFT)
                    elif e.key == K_RIGHT:
                        player.stop(RIGHT)

                elif e.type == QUIT:
                    self.quit()

            allsprites.update()
            allsprites._spritelist.sort(key=lambda s: s.pos[Y])

##            allsprites.clear(screen, self.draw_background)
            self.draw_background(screen)
            updates = allsprites.draw(screen)

############# Debug drawing
##            pygame.draw.rect(screen, (0, 0, 0), player.get_swordrect(), 1)
##            for s in allsprites:
##                pygame.draw.rect(screen, (0, 0, 0), s.rect, 1)
##                pygame.draw.rect(screen, (0, 0, 0), s.boundrect, 1)
##                pygame.draw.circle(screen, (0, 0, 0), s.pos, 2)
############# End

            pygame.display.update()

def main():
    Game().main()

if __name__ == '__main__':
    try:
        main()
    finally:
        pygame.quit()
