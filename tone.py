#!/usr/bin/env python3
import sys, re, argparse
import numpy as np
import pygame as pg

def tone_array(freq, duration=1.0, amp=0.5, shape='sine', mixer_opts=None):
    pg.mixer.init(**mixer_opts or {})
    sfreq, size, channels = pg.mixer.get_init() # or (22050, -16, 2)
    sign, size = size < 0, abs(size)
    dtype = np.dtype('ui'[sign] + str(size//8))
    amax = (1 << size-1) - 1
    amp *= amax
    off = 0 if sign else 1 << size-1
    t = np.arange(0, duration, 1/sfreq)
    if callable(shape):
        a = shape(freq*t)
    elif shape == 'sine':
        a = np.sin(2*np.pi*freq*t)
    elif shape == 'square':
        a = 1 - 2*np.floor(2*freq*t % 2)
    elif shape in ('tri', 'triangle'):
        a = abs((4*freq*t - 1) % 4 - 2) - 1
    elif shape in ('saw', 'sawtooth'):
        a = (freq*t - .5) % 1 * 2 - 1
    elif shape == ('circle'):
        a = np.sqrt(1 - (4*freq*t % 2 - 1)**2) * (-1)**np.floor(2*freq*t)
    else:
        raise ValueError('invalid shape: %s' % shape)
    a = np.around(a*amp + off).clip(-amax, amax).astype(dtype)
    if channels == 2:
        a = np.column_stack((a, a))
    return a

def tone(freq, duration=1.0, amp=.5, shape='sine', mixer_opts=None):
    return pg.sndarray.make_sound(
        tone_array(freq, duration, amp, shape, mixer_opts))

notes = {'Cb': -1, 'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
         'E#': 5, 'Fb': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
         'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'B#': 12}

def note2freq(note):
    try:
        return float(note)
    except ValueError:
        try:
            name, i = re.match(r'^([A-Ga-g][#b]?)(-?\d+)?$', note).groups()
        except AttributeError:
            raise ValueError('invalid note: %s' % note) from None
        i = int(i) if i else 4
        name = name[0].upper() + name[1:]
        midi = 12*(i + 1) + notes[name]
        return 440.0 * 2**((midi-69)/12)

def play(freq='C5', duration=1.0, amp=0.5, shape='sine', mixer_opts=None):
    # Note: on windows, playing without a window only seems to work if the
    # rest of pygame is *not* initialized
    pg.mixer.init(**mixer_opts or {})
    if isinstance(freq, pg.mixer.Sound):
        t = freq
    elif isinstance(freq, np.ndarray):
        t = pg.sndarray.make_sound(freq)
    else:
        freq = note2freq(freq)
        t = tone(freq, duration, amp, shape)
    t.play()
    pg.time.wait(int(t.get_length()*1000))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('freq', nargs='*', default=['C5'], type=note2freq)
    p.add_argument('-d', '--duration', type=float, default=1.0)
    p.add_argument('-a', '--amplitude', type=float, default=0.5)
    p.add_argument('-s', '--shape', default='sine')
    args = p.parse_args()
    for freq in args.freq:
        play(freq, args.duration, args.amplitude, args.shape)
