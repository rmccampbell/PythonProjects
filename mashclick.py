#!/usr/bin/python3
import pyautogui, time, argparse, random

def mash_click(freq=100.0, duration=None, x=None, y=None, radius=80,
               randomness=0.):
    dt = 1.0/freq
    pyautogui.moveTo(x, y)
    x, y = pyautogui.position()
    if duration:
        endtime = time.time() + duration
    try:
        while not duration or time.time() < endtime:
            x2, y2 = pyautogui.position()
            if max(abs(x2 - x), abs(y2 - y)) > radius:
                break
            interv = dt + (randomness and random.random()*randomness)
            pyautogui.click(interval=interv)
    except (KeyboardInterrupt, pyautogui.FailSafeException):
        pass

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('freq', type=float, default=100.0, nargs='?',
                   help='default: %(default)s')
    p.add_argument('duration', type=float, nargs='?')
    p.add_argument('x', type=int, nargs='?')
    p.add_argument('y', type=int, nargs='?')
    p.add_argument('-r', '--radius', type=int, default=100,
                   help='default: %(default)s')
    p.add_argument('-R', '--randomness', type=float, default=0.,
                   help='default: %(default)s')
    args = p.parse_args()
    mash_click(**vars(args))
