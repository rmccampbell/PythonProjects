#!/usr/bin/env python3
import time, json, itertools
import pymouse, pykeyboard

# Note: High DPI scaling must be disabled for python.exe on windows

class Recorder:
    def __init__(self):
        super().__init__()
        self.events = []
        self.starttime = self.time = 0

    def run(self):
        self.starttime = self.time = time.perf_counter()
        super().run()

    def run_until_escape(self):
        if not self.is_alive():
            self.start()
        escaper = pykeyboard.PyKeyboardEvent()
        escaper.start()
        try:
            escaper.join()
        except KeyboardInterrupt:
            pass
        self.stop()
        self.join()

    def tick(self):
        ctime = time.perf_counter()
        dtime = ctime - self.time
        self.time = ctime
        return dtime

    def tottime(self):
        return self.time - self.starttime

    def stop(self):
        super().stop()
        self.events.append(('wait', self.tick()))

    def save(self, file=None):
        return save(file, self.events)


class MouseRecorder(Recorder, pymouse.PyMouseEvent):
    def __init__(self, track_movement=True):
        super().__init__()
        self.track_movement = track_movement

    def click(self, x, y, button, press):
        self.events.append(('click', self.tick(), x, y, button, press))

    def scroll(self, x, y, vert, horiz):
        self.events.append(('scroll', self.tick(), x, y, vert, horiz))

    def move(self, x, y):
        if self.track_movement:
            self.events.append(('move', self.tick(), x, y))


class KeyRecorder(Recorder, pykeyboard.PyKeyboardEvent):
    def __init__(self, escape_key=None, remove_dups=True):
        super().__init__()
        self.escape_key = escape_key
        self.remove_dups = remove_dups
        self.pressed_keys = set()

    def run_until_escape(self):
        if not self.is_alive():
            self.start()
        self.join()

    def tap(self, keycode, character, press):
        if self.remove_dups and press and keycode in self.pressed_keys:
            return
        self.events.append(('key', self.tick(), keycode, character, press))
        if press:
            self.pressed_keys.add(keycode)
        else:
            self.pressed_keys.discard(keycode)

    def escape(self, event):
        if self.escape_key is not None:
            return event.KeyID == self.escape_key
        return super().escape(event)

recorder = None

def record(keys=False, track_movement=True, escape_key=None, blocking=True):
    global recorder
    recorder = KeyRecorder(escape_key) if keys else MouseRecorder(track_movement)
    recorder.start()
    if blocking:
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
        json.dump(events, file, indent=1)
    return getattr(file, 'name', None)

def load(file):
    global recorder
    if isinstance(file, str):
        file = open(file, 'r')
    with file:
        events = json.load(file)
    if recorder is None:
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
    keyboard = pykeyboard.PyKeyboard()
    escaper = pykeyboard.PyKeyboardEvent()
    escaper.start()
    tottime = realtime = 0.0
    starttime = time.perf_counter()
    for event in events:
        # keyboard event stops on escape key
        if not escaper.is_alive():
            return False, tottime
        type, dtime, *rest = event
        tottime += dtime
        realtime = time.perf_counter() - starttime
        time.sleep(max(tottime / speed - realtime, 0))
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
        elif type == 'key':
            keycode, character, press = rest
            if press:
                keyboard.press_key(keycode)
            else:
                keyboard.release_key(keycode)
        elif type == 'wait':
            pass
    return True, realtime

def macro_length(events):
    return sum(event[1] for event in events)

def macro_slice(events, starttime=0.0, endtime=float('inf')):
    curtime = 0
    newevents = []
    for event in events:
        curtime += event[1]
        if curtime > endtime:
            break
        elif curtime >= starttime:
            newevents.append(event)
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
    p1.add_argument('-k', '--keys', action='store_true')
    p1.add_argument('-T', '--no-track', action='store_true')
    p1.add_argument('-e', '--escape-key', type=int)

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
        recorder = record(keys=args.keys, track_movement=not args.no_track,
                          escape_key=args.escape_key, blocking=True)
        print('\aStopped: {:.2f} s'.format(recorder.tottime()))
        print('Saved:', recorder.save(args.file))

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
            json.dump(events, f3, indent=1)

    elif args.command in ('length', 'len'):
        with open(args.file) as f:
            events = json.load(f)
            print(macro_length(events))

    elif args.command == 'slice':
        with open(args.file) as f1:
            events = json.load(f1)
        newevents = macro_slice(events, args.starttime, args.endtime)
        with open(args.outfile, 'w') as f2:
            json.dump(newevents, f2, indent=1)

    elif args.command == 'speed':
        with open(args.file) as f1:
            events = json.load(f1)
        newevents = macro_speedup(events, args.speed)
        with open(args.outfile, 'w') as f2:
            json.dump(newevents, f2, indent=1)
