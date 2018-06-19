#!/usr/bin/env python3
import time, json, itertools
import pymouse, pykeyboard

# Note: High DPI scaling must be disabled for python.exe on windows

class MouseRecorder(pymouse.PyMouseEvent):
    def __init__(self, track_movement=True):
        super().__init__()
        self.events = []
        self.track_movement = track_movement

    def run(self):
        self.time = time.time()
        super().run()

    def run_until_escape(self):
        if not self.is_alive():
            self.start()
        escaper = pykeyboard.PyKeyboardEvent()
        escaper.start()
        try:
            while escaper.is_alive():
                time.sleep(.1)
        except KeyboardInterrupt:
            pass
        self.stop()
        self.join()

    def tick(self):
        ctime = time.time()
        dtime = ctime - self.time
        self.time = ctime
        return dtime

    def click(self, x, y, button, press):
        self.events.append(('click', self.tick(), x, y, button, press))

    def scroll(self, x, y, vert, horiz):
        self.events.append(('scroll', self.tick(), x, y, vert, horiz))

    def move(self, x, y):
        if self.track_movement:
            self.events.append(('move', self.tick(), x, y))

    def stop(self):
        super().stop()
        self.events.append(('wait', self.tick()))

    def save(self, file=None):
        save(file, self.events)

recorder = None

def record(track_movement=True, run_until_escape=True):
    global recorder, escaper
    recorder = MouseRecorder(track_movement)
    recorder.start()
    if run_until_escape:
        recorder.run_until_escape()
    return recorder

def stop():
    global recorder
    recorder.stop()

def _find_file():
    for i in range(100):
        try:
            return open('macro{}.json'.format(i), 'x')
        except FileExistsError as e:
            err = e
    raise err

def save(file=None, events=None):
    if file is None:
        file = _find_file()
    elif isinstance(file, str):
        file = open(file, 'w')
    if events is None:
        events = recorder.events
    with file:
        json.dump(events, file)

def load(file):
    global recorder
    if isinstance(file, str):
        file = open(file, 'r')
    with file:
        events = json.load(file)
        if recorder == None:
            recorder = MouseRecorder()
        recorder.events = events
        return events

def playback(events=None, speed=1.0, repeat=False):
    global recorder
    if events is None:
        events = recorder.events
    if repeat:
        events = itertools.cycle(events)
    mouse = pymouse.PyMouse()
    escaper = pykeyboard.PyKeyboardEvent()
    escaper.start()
    tottime = 0.0
    for event in events:
        # keyboard event stops on escape key
        if not escaper.is_alive():
            return False, tottime
        type, dtime, *rest = event
        tottime += dtime
        time.sleep(dtime / speed)
        if type == 'click':
            x, y, button, press = rest
            if press:
                mouse.press(x, y, button)
            else:
                mouse.release(x, y, button)
        elif type == 'scroll':
            x, y, vert, horiz = rest
            mouse.move(x, y)
            mouse.scroll(vert, horiz)
        elif type == 'move':
            x, y = rest
            mouse.move(x, y)
        elif type == 'wait':
            pass
    return True, tottime

def macro_length(events):
    return sum(event[1] for event in events)

def macro_slice(events, starttime=0.0, endtime=float('inf')):
    curtime = 0
    newevents = []
    for event in events:
        curtime += event[1]
        if starttime <= curtime <= endtime:
            newevents.append(event)
        elif curtime > endtime:
            break
    return newevents

def macro_speedup(events, speed=1.0):
    return [(typ, dtime / speed, *rest) for typ, dtime, *rest in events]


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='command')
    sp.required = True

    p1 = sp.add_parser('record')
    p1.add_argument('file', nargs='?')
    p1.add_argument('-T', '--no-track', action='store_true')

    p2 = sp.add_parser('play')
    p2.add_argument('file')
    p2.add_argument('-s', '--speed', type=float, default=1.0)
    p2.add_argument('-r', '--repeat', action='store_true')

    p3 = sp.add_parser('concat')
    p3.add_argument('file1')
    p3.add_argument('file2')
    p3.add_argument('outfile')
    p3.add_argument('-d', '--delay', type=float, default=0.0)

    p4 = sp.add_parser('length', aliases=['len'])
    p4.add_argument('file')

    p5 = sp.add_parser('slice')
    p5.add_argument('file')
    p5.add_argument('outfile')
    p5.add_argument('starttime', type=float)
    p5.add_argument('endtime', type=float, nargs='?', default=float('inf'))

    p5 = sp.add_parser('speed')
    p5.add_argument('file')
    p5.add_argument('outfile')
    p5.add_argument('speed', type=float)

    args = p.parse_args()

    if args.command == 'record':
        print('Recording...')
        recorder = record(track_movement=not args.no_track,
                          run_until_escape=True)
        recorder.save(args.file)
        print('\aSaved')

    elif args.command == 'play':
        print('Playing...')
        events = load(args.file)
        finished, tottime = playback(events, args.speed, args.repeat)
        msg = 'Finished' if finished else 'Interrupted'
        print('\a{}: {:.2f} s'.format(msg, tottime))

    elif args.command == 'concat':
        with open(args.file1) as f1, open(args.file2) as f2:
            events = json.load(f1)
            events2 = json.load(f2)
        if args.delay:
            events.append(('wait', args.delay))
        events += events2
        with open(args.outfile, 'w') as f3:
            json.dump(events, f3)

    elif args.command in ('length', 'len'):
        with open(args.file) as f:
            events = json.load(f)
            print(macro_length(events))

    elif args.command == 'slice':
        with open(args.file) as f1:
            events = json.load(f1)
        newevents = macro_slice(events, args.starttime, args.endtime)
        with open(args.outfile, 'w') as f2:
            json.dump(newevents, f2)

    elif args.command == 'speed':
        with open(args.file) as f1:
            events = json.load(f1)
        newevents = macro_speedup(events, args.speed)
        with open(args.outfile, 'w') as f2:
            json.dump(newevents, f2)
