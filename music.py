#!/usr/bin/env python3
import pygame, sys, os
from pygame.locals import *

def load_sound(name):
    base = os.path.dirname(__file__)
    fullname = os.path.join(base, 'data', 'sounds', name + '.wav')
    return pygame.mixer.Sound(fullname)

class Note(pygame.sprite.Sprite):
    def __init__(self, pitch):
        self.pitch = pitch
        self.sound = sounds[pitch]

        self.y = 415 - (pitch * 50)
        self.x = 650
        self.speed = 4
        self.color = Color(0, 0, 255)
        self.active = False
        self.hit = False
        self.missed = False
        super().__init__()

    def update(self, surface):
        self.x -= self.speed
        if self.x < 120 and self.x >= 90 and not self.active:
            self.active = True
        if self.x < 90 and self.active:
            self.active = False
            if not self.hit: self.miss()
        if self.x < -10:
            self.kill()

        self.draw(surface)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), 10)

    def hit_note(self):
        self.hit = True
        self.sound.play()
        self.color = Color(0, 255, 0)

    def miss(self):
        global mistakes
        self.missed = True
        self.color = Color(255, 0, 0)
        mistakes += 1

sounds = {}

song = [3, 3, 4, 5, 5, 4, 3, 2, 1, 1, 2, 3, 3, 2, 2, 0,
        3, 3, 4, 5, 5, 4, 3, 2, 1, 1, 2, 3, 2, 1, 1]

mistakes = 0

def main():
    def hit_note(pitch):
        for note in notes:
            if note.active:
                if note.pitch == pitch:
                    note.hit_note()
                    return
        false_hit()

    def false_hit():
        global mistakes
        mistakes += 1

    pygame.init()
    screen = pygame.display.set_mode((640,480))

    #Load sounds
    sounds.update({
        1: load_sound('c_note'),
        2: load_sound('d_note'),
        3: load_sound('e_note'),
        4: load_sound('f_note'),
        5: load_sound('g_note'),
        6: load_sound('a_note'),
        7: load_sound('b_note'),
    })

    duration = 20
    position = 0
    timer = 0

    notes = pygame.sprite.OrderedUpdates()

    clock = pygame.time.Clock()
    running = True
    
    while running:
        clock.tick(30)

        #Handle events
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                #Test for hit notes
                if event.key == K_1:
                    hit_note(1)
                if event.key == K_2:
                    hit_note(2)
                if event.key == K_3:
                    hit_note(3)
                if event.key == K_4:
                    hit_note(4)
                if event.key == K_5:
                    hit_note(5)

                elif event.key == K_ESCAPE or \
                     event.key == K_F4 and event.mod & KMOD_ALT:
                    running = False

            elif event.type == QUIT:
                running = False

        #Track position and create new Notes
        if timer == 0:
            if position < len(song):
                pitch = song[position]
                if pitch > 0:
                    notes.add(Note(pitch))
                position += 1
            timer = duration
        timer -= 1

        screen.fill((255, 255, 255))

        #Draw background
        for y in range(115, 366, 50):
            pygame.draw.line(screen, (191, 191, 255), (0, y),
                             (screen.get_width(), y), 3)

        #Update and draw notes
        notes.update(screen)

        #Draw foreground
        pygame.draw.line(screen, (0, 0, 0), (90, 0),
                         (90, screen.get_height()), 3)
        pygame.draw.line(screen, (0, 0, 0), (120, 0),
                         (120, screen.get_height()), 3)

        pygame.display.flip()

        #Too many mistakes
        if mistakes >= 5:
            print('You lose')
            running = False

        #End of song
        if len(notes) == 0 and position >= len(song):
            print('You win!')
            running = False

if __name__ == '__main__':
    main()
    pygame.quit()
