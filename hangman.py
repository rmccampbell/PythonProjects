#!/usr/bin/env python3
import curses, random
from urllib.request import urlopen

WORDS_URL = 'https://raw.githubusercontent.com/Xethron/Hangman/master/words.txt'

HANGMAN_TEMPLATE = R'''
 ┌──┐
 │  ☻
 │ ─┼─
 │ / \
─┴────
'''[1:-1]
HANGMAN_MASK = R'''
 ┌──┐
 │  1
 │ 324
 │ 5 6
─┴────
'''[1:-1]

class Hangman:
    def __init__(self, scr):
        curses.curs_set(0)
        self.win = scr
        h, w = scr.getmaxyx()
        self.win = scr.subwin(13, 24, (h-1)//2 - 6, (w-1)//2 - 12)

        with urlopen(WORDS_URL) as req:
            self.wordlist = req.read().decode().splitlines()

        self.reset()

        while True:
            self.draw()
            k = scr.getkey()
            # Escape, ^Q, ^C
            if k in ('\x1b', '\x11', '\x03') or self.gameover and k == 'q':
                break
            if k in ('\x12') or self.gameover and k == 'r':
                self.reset()
            elif k.isalpha() and not self.gameover:
                k = k.lower()
                if k not in self.word and k not in self.guesses:
                    self.num_failures += 1
                self.guesses.add(k)
            if set(self.word) <= self.guesses:
                self.won = True
                self.gameover = True
            if self.num_failures >= 6:
                self.won = False
                self.gameover = True

    def reset(self):
        self.won = False
        self.gameover = False
        self.num_failures = 0
        self.guesses = set()
        self.word = random.choice(self.wordlist)

    def draw(self):
        win = self.win
        win.clear()
        win.border()
        hangman_s = ''.join(
            c if (not d.isdigit()) or (self.num_failures >= int(d)) else ' '
            for c, d in zip(HANGMAN_TEMPLATE, HANGMAN_MASK)
        )
        for i, line in enumerate(hangman_s.splitlines()):
            win.addstr(2+i, 4, line)
        word_s = ''.join(c if c in self.guesses else '_' for c in self.word)
        win.addstr(8, 4, word_s)
        wrong_guesses = self.guesses - set(self.word)
        guesses_s = ''.join(sorted(wrong_guesses))
        win.addstr(9, 4, guesses_s, curses.A_STANDOUT)
        if self.gameover:
            if self.won:
                win.addstr(10, 4, 'You won!')
            else:
                win.addstr(10, 4, 'You lost!')
        win.refresh()

if __name__ == '__main__':
    curses.wrapper(Hangman)
