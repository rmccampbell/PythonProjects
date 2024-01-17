#!/usr/bin/env python3

import pathlib
import time
import curses
from curses import ascii
import numpy as np
import imageio.v3 as iio
import soundfile
import sounddevice

DATA = pathlib.Path(__file__).parent / 'data'
VIDEO_PATH = DATA / 'bad_apple.mp4'
AUDIO_PATH = DATA / 'bad_apple_enhanced.mp3'

QUIT_KEYS = {ascii.ESC, ord('q')}

def img_to_str(img: np.ndarray):
    """Convert binary image (0/1) to block characters"""
    lines = []
    for i in range(0, img.shape[0], 2):
        line = []
        for j in range(img.shape[1]):
            upper, lower = img[i:i+2, j]
            char = ' ▄▀█'[2*upper + lower]
            line.append(char)
        lines.append(''.join(line))
    return '\n'.join(lines)

def main(scr: curses.window):
    curses.curs_set(0)
    scr.nodelay(True)
    ssize = np.array(scr.getmaxyx()) * [2, 1]

    audio, sr = soundfile.read(AUDIO_PATH)
    try:
        sounddevice.play(audio, sr)
    except sounddevice.PortAudioError:
        pass

    with iio.imopen(VIDEO_PATH, 'r') as reader:
        fsize = np.array(reader.properties().shape[1:3])
        reduce = int(np.ceil(fsize / ssize).max())
        fps = reader.metadata().get('fps', 30)
        dur = 1/fps

        nexttime = time.monotonic()
        for frame in reader.iter():
            if scr.getch() in QUIT_KEYS:
                break

            pixelized = frame[::reduce, ::reduce, 0] >= 128
            string = img_to_str(pixelized)
            scr.addstr(0, 0, string)

            time.sleep(max(nexttime - time.monotonic(), 0))
            nexttime += dur
            scr.refresh()

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
