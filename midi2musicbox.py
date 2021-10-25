import os
import argparse
import bisect
import midi
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
import warnings

TOPMARGIN = 5*mm
LEFTMARGIN = 5*mm
NOTEWIDTH = 2*mm
NOTELENGTH = 8*mm # Length of quarter note
RADIUS = 1*mm
PAGEHEIGHT = LETTER[1]

QNOTES_PER_PAGE = int((PAGEHEIGHT - TOPMARGIN) // NOTELENGTH)

# C D G A B C D E F F# G G# A A# B C C# D D# E F F# G G# A A# B C D E
NOTES = [48, 50, 55, 57, 59, 60, 62, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73,
         74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 86, 88]

NOTEMAP = {note: ind for ind, note in enumerate(NOTES)}

COLORS = [colors.green, colors.blue, colors.orange, colors.yellow, colors.violet, colors.red]

def midi2points(file, tracks=None, octaves=0, mode='drop', scale=1, delay=0):
    assert mode in ['drop', 'shift', 'middle']
    midifile = midi.MidiFile.read(file)
    tracks = [midifile.tracks[i] for i in tracks] if tracks else midifile.tracks
    points = []
    if isinstance(octaves, int):
        octaves = [octaves] * len(tracks)
    assert len(octaves) == len(tracks)
    for tnum, (octave, track) in enumerate(zip(octaves, tracks)):
        track = track.to_abs()
        for event, tick in track:
            if event[0] & 0xf0 == midi.NoteOn and event[2] > 0:
                note = event[1]
                x, good = resolve_note(note, octave, mode)
                if x is not None:
                    y = tick * scale / midifile.division + delay
                    points.append((y, x, tnum, good))
    return points

def resolve_note(note, octave=0, mode='drop'):
    note += octave*12
    good = True
    if note not in NOTEMAP:
        good = False
        if mode == 'shift':
            d = 12 if note < 64 else -12
            while note not in NOTEMAP:
                note += d
        elif mode == 'middle':
            return bisect.bisect_left(NOTES, note) - .5, good
        else: # drop
            warnings.warn(f'Note dropped: {note}')
            return None, good
    return NOTEMAP[note], good

def draw_grid(c):
    left = LEFTMARGIN
    right = left + NOTEWIDTH*(len(NOTES) - 1)
    top = PAGEHEIGHT - TOPMARGIN
    bottom = top - NOTELENGTH*QNOTES_PER_PAGE
    for y in range(QNOTES_PER_PAGE):
        py = top - y*NOTELENGTH
        c.line(left, py, right, py)
        py2 = py - NOTELENGTH/2
        c.setDash(4*mm, 2*mm)
        c.line(left, py2, right, py2)
        c.setDash(1, 0)
    c.line(left, bottom, right, bottom)
    for x in range(len(NOTES)):
        px = LEFTMARGIN + x*NOTEWIDTH
        c.line(px, top, px, bottom)

def render_pdf(points, outfile):
    points = sorted(points)
    c = Canvas(outfile, pagesize=LETTER)
    page = 0
    draw_grid(c)
    for y, x, tnum, good in points:
        newpage = y // QNOTES_PER_PAGE
        if newpage > page:
            c.showPage()
            page += 1
            draw_grid(c)
        y %= QNOTES_PER_PAGE
        px = x*NOTEWIDTH + LEFTMARGIN
        py = PAGEHEIGHT - TOPMARGIN - y*NOTELENGTH
        c.setFillColor(COLORS[tnum % len(COLORS)])
        if not good:
            c.setStrokeColor(colors.red)
        c.circle(px, py, RADIUS, stroke=1, fill=1)
        c.setStrokeGray(0)
        c.setFillGray(0)
    c.save()

def midi2musicbox(file, outfile, tracks=None, octaves=0, mode='drop', scale=1, delay=0):
    points = midi2points(file, tracks, octaves, mode, scale, delay)
    render_pdf(points, outfile)


def int_or_int_list(s):
    return int_list(s) if ',' in s else int(s)

def int_list(s):
    return [int(x) for x in s.split(',')]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('file')
    p.add_argument('outfile', nargs='?')
    p.add_argument('-t', '--tracks', type=int_list)
    p.add_argument('-o', '--octaves', type=int_or_int_list, default=0)
    p.add_argument('-S', '--shift', dest='mode', action='store_const',
                   const='shift', default='drop')
    p.add_argument('-m', '--middle', dest='mode', action='store_const',
                   const='middle', default='drop')
    p.add_argument('-s', '--scale', type=float, default=1)
    p.add_argument('-d', '--delay', type=float, default=0)
    args = p.parse_args()
    outfile = args.outfile or os.path.splitext(args.file)[0] + '.pdf'
    midi2musicbox(args.file, outfile, args.tracks, args.octaves, args.mode,
               args.scale, args.delay)
