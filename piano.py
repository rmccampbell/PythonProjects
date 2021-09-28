#!/usr/bin/env python3
import midi
import curses
from curses import ascii
import argparse
import threading

keyboard = '''\
┌───┬───┬─┬───┬───┬───┬───┬─┬───┬─┬───┬───┬───┬───┬─┬───┬───┬────┐
│   │   │ │   │   │   │   │ │   │ │   │   │   │   │ │   │   │    │
│   │ W │ │ E │   │   │ T │ │ Y │ │ U │   │   │ O │ │ P │   │    │
│   └─┬─┘ └─┬─┘   │   └─┬─┘ └─┬─┘ └─┬─┘   │   └─┬─┘ └─┬─┘   │    │
│  A  │  S  │  D  │  F  │  G  │  H  │  J  │  K  │  L  │  ;  │ '  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴────┘
'''
keyboard_w = len(keyboard.splitlines()[0])
keyboard_h = len(keyboard.splitlines())

keys = "awsedftgyhujkolp;'"
# C4 - F5
notes = range(60, 60+len(keys))
key2note = dict(zip(map(ord, keys), notes))

def draw_piano(win: 'curses.window'):
    for i, row in enumerate(keyboard.splitlines()):
        win.addstr(i, 0, row)

def main(scr: 'curses.window', midi_port=None, key_dur=.25):
    mp = midi.MidiPlayer(midi_port)
    curses.curs_set(0)
    scrh, scrw = scr.getmaxyx()
    win = scr.subwin((scrh - keyboard_h)//2, (scrw - keyboard_w)//2)
    draw_piano(win)
    while True:
        key = win.getch()
        if key in {ord('q'), ascii.ctrl(ord('C')), ascii.ESC}:
            break
        note = key2note.get(key)
        if note:
            threading.Thread(target=mp.play_note, args=(note, key_dur)).start()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', type=int, help='Midi port')
    p.add_argument('-d', '--key-dur', type=float, default=.25, help='Key press duration')
    args = p.parse_args()
    curses.wrapper(main, args.port, args.key_dur)
