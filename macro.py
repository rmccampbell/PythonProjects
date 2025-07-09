#!/usr/bin/env python3
import os, time, json, itertools, enum
import pymouse, pykeyboard

# Note: High DPI scaling must be disabled for python.exe on windows

class Mode(enum.Enum):
    MOUSE = 'mouse'
    KEYS = 'keys'

    def __str__(self):
        return self.value

class Recorder:
    def __init__(self, init_events=None, verbose=False):
        super().__init__()
        self.events = list(init_events) if init_events else []
        self.starttime = self.time = 0
        self.verbose = verbose

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
            escaper.stop()
        self.stop()
        self.join()

    def add_event(self, typ, **attrs):
        event = make_event(typ, self.tick(), **attrs)
        self.events.append(event)
        if self.verbose:
            print(event)

    def tick(self):
        ctime = time.perf_counter()
        dtime = ctime - self.time
        self.time = ctime
        return dtime

    def tottime(self):
        return self.time - self.starttime

    def stop(self):
        super().stop()
        self.add_event('wait')

    def save(self, file=None, overwrite=False):
        return save(file, self.events, overwrite)

    def load(self, file):
        self.events = load(file)


class MouseRecorder(Recorder, pymouse.PyMouseEvent):
    def __init__(self, *, track_movement=True, init_events=None,
                 verbose=False):
        super().__init__(init_events, verbose)
        self.track_movement = track_movement

    def click(self, x, y, button, press):
        self.add_event('click', x=x, y=y, button=button, press=press)

    def scroll(self, x, y, vert, horiz):
        self.add_event('scroll', x=x, y=y, vert=vert, horiz=horiz)

    def move(self, x, y):
        if self.track_movement:
            self.add_event('move', x=x, y=y)


class KeyRecorder(Recorder, pykeyboard.PyKeyboardEvent):
    def __init__(self, escape_key=None, *, remove_dups=True, init_events=None,
                 verbose=False):
        super().__init__(init_events, verbose)
        self.escape_key = escape_key
        self.remove_dups = remove_dups
        self.pressed_keys = set()

    def run_until_escape(self):
        if not self.is_alive():
            self.start()
        self.join()

    def tap(self, keycode, character, press):
        if (self.escape_key is not None
                and self.escape_key in (keycode, character)):
            self.stop()
            return
        if self.remove_dups and press and keycode in self.pressed_keys:
            return
        self.add_event('key', keycode=keycode, character=character, press=press)
        if press:
            self.pressed_keys.add(keycode)
        else:
            self.pressed_keys.discard(keycode)

    def escape(self, event):
        if self.escape_key is not None:
            # Handle custom escape key in tap for compatibility
            return False
        return super().escape(event)


class MouseTrigger(pymouse.PyMouseEvent):
    def __init__(self, num_clicks=1):
        super().__init__()
        self.num_clicks = num_clicks
        self.trigger_time = None

    def wait(self):
        self.start()
        self.join()
        return self.trigger_time

    def click(self, x, y, button, press):
        if button != 1 or not press:
            return
        self.num_clicks -= 1
        if self.num_clicks == 0:
            self.trigger_time = time.perf_counter()
            self.stop()


def make_event(typ, dtime, **attrs):
    return {'type': typ, 'dtime': dtime, **attrs}


recorder = None

def record(mode=Mode.MOUSE, track_movement=True, escape_key=None, blocking=True,
           init_events=None, verbose=False):
    global recorder
    kwargs = {'init_events': init_events, 'verbose': verbose}
    if mode == Mode.KEYS:
        recorder = KeyRecorder(escape_key=escape_key, **kwargs)
    else:
        recorder = MouseRecorder(track_movement=track_movement, **kwargs)
    recorder.start()
    if blocking:
        recorder.run_until_escape()
    return recorder

def stop():
    global recorder
    recorder.stop()

def _find_file():
    i = 0
    while True:
        try:
            return open('macro{}.json'.format(i), 'x')
        except FileExistsError:
            i += 1

def save(file=None, events=None, overwrite=False):
    if not file:
        file = _find_file()
    elif isinstance(file, str):
        file = open(file, 'w' if overwrite else 'x')
    if events is None:
        events = recorder.events
    with file:
        json.dump(events, file, indent=1)
    return getattr(file, 'name', None)

def load(file):
    if isinstance(file, str):
        file = open(file, 'r')
    with file:
        events = json.load(file)
    return events

def playback(events=None, speed=1.0, repeat=False, starttime=0.0,
             endtime=float('inf'), skip=0, start_on_click=0, status=True):
    global recorder
    if events is None:
        events = recorder.events
    if starttime or endtime != float('inf'):
        events = macro_slice(events, starttime, endtime)
    nevents = len(events)
    if repeat:
        events = itertools.cycle(events)
    mouse = pymouse.PyMouse()
    keyboard = pykeyboard.PyKeyboard()
    escaper = pykeyboard.PyKeyboardEvent()
    escaper.start()
    tottime = realtime = 0.0
    if start_on_click:
        if start_on_click > 1:
            print(f'Click {start_on_click} times to start playback...')
        else:
            print('Click to start playback...')
        begintime = MouseTrigger(start_on_click).wait()
    else:
        begintime = time.perf_counter()
    if status:
        print(f'0/{nevents}', end='', flush=True)
    try:
        for i, event in enumerate(events):
            # keyboard event stops on escape key
            if not escaper.is_alive():
                return False, tottime
            typ = event['type']
            tottime += event['dtime']
            if skip > 0:
                skip -= 1
                continue
            realtime = time.perf_counter() - begintime
            time.sleep(max(tottime / speed - realtime, 0))
            if typ == 'click':
                if event['press']:
                    mouse.press(event['x'], event['y'], event['button'])
                else:
                    mouse.release(event['x'], event['y'], event['button'])
            elif typ == 'scroll':
                mouse.move(event['x'], event['y'])
                mouse.scroll(event['vert'], event['horiz'])
            elif typ == 'move':
                mouse.move(event['x'], event['y'])
            elif typ == 'key':
                if event['press']:
                    keyboard.press_key(event['keycode'])
                else:
                    keyboard.release_key(event['keycode'])
            elif typ == 'wait':
                pass
            if status:
                print(f'\r{i+1}/{nevents}', end='', flush=True)
    finally:
        if status:
            print()
    return True, tottime

def macro_length(events):
    return sum(event['dtime'] for event in events)

def macro_slice(events, starttime=0.0, endtime=float('inf')):
    curtime = 0
    newevents = []
    for event in events:
        curtime += event['dtime']
        if curtime > endtime:
            break
        elif curtime >= starttime:
            newevents.append(event)
    return newevents

def macro_speedup(events, speed=1.0):
    return [{**evt, 'dtime': evt['dtime'] / speed} for evt in events]

def _prompt_resolve_file(file, overwrite):
    while not overwrite and file and os.path.exists(file):
        res = input(f'{file} already exists. Overwrite? (y/[n]): ')
        if res.strip().casefold().startswith('y'):
            overwrite = True
        else:
            file = input('Choose another filename: ')
    return file, overwrite


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='command', required=True)

    p1 = sp.add_parser('record')
    p1.add_argument('mode', type=Mode, choices=list(Mode))
    p1.add_argument('file', nargs='?')
    p1.add_argument('-T', '--no-track', action='store_true')
    p1.add_argument('-e', '--escape-key', type=int)
    p1.add_argument('-E', '--escape-char')
    p1.add_argument('-v', '--verbose', action='store_true')
    p1.add_argument('-a', '--append')
    p1.add_argument('-o', '--overwrite', action='store_true')

    p2 = sp.add_parser('play')
    p2.add_argument('file')
    p2.add_argument('-s', '--speed', type=float, default=1.0)
    p2.add_argument('-r', '--repeat', action='store_true')
    p2.add_argument('-S', '--starttime', type=float, default=0)
    p2.add_argument('-E', '--endtime', type=float, default=float('inf'))
    p2.add_argument('-k', '--skip', type=int, default=0)
    p2.add_argument('-c', '--start-on-click', type=int, nargs='?', const=1)

    p3 = sp.add_parser('concat')
    p3.add_argument('file1')
    p3.add_argument('file2')
    p3.add_argument('outfile')
    p3.add_argument('-d', '--delay', type=float, default=0.0)
    p3.add_argument('-o', '--overwrite', action='store_true')

    p4 = sp.add_parser('length', aliases=['len'])
    p4.add_argument('file')

    p5 = sp.add_parser('slice')
    p5.add_argument('file')
    p5.add_argument('outfile')
    p5.add_argument('starttime', type=float)
    p5.add_argument('endtime', type=float, nargs='?', default=float('inf'))
    p5.add_argument('-o', '--overwrite', action='store_true')

    p6 = sp.add_parser('speedup', aliases=['speed'])
    p6.add_argument('file')
    p6.add_argument('outfile')
    p6.add_argument('speed', type=float)
    p6.add_argument('-o', '--overwrite', action='store_true')

    args = p.parse_args()

    if args.command == 'record':
        print('Recording...')
        init_events = None
        if args.append:
            init_events = load(args.append)
        if args.mode == Mode.MOUSE:
            kwargs = {'track_movement': not args.no_track}
        else:
            kwargs = {'escape_key': args.escape_key or args.escape_char}
        recorder = record(args.mode, blocking=True, init_events=init_events,
                          verbose=args.verbose, **kwargs)
        print('\aStopped: {:.2f} s'.format(recorder.tottime()))
        try:
            file, overwrite = _prompt_resolve_file(args.file, args.overwrite)
            print('Saved:', recorder.save(file, overwrite))
        except KeyboardInterrupt:
            pass

    elif args.command == 'play':
        print('Playing...')
        events = load(args.file)
        finished, tottime = playback(
            events, args.speed, args.repeat, args.starttime, args.endtime,
            args.skip, args.start_on_click)
        msg = 'Finished' if finished else 'Interrupted'
        print('\a{}: {:.2f} s'.format(msg, tottime))

    elif args.command == 'concat':
        events = load(args.file1)
        events2 = load(args.file2)
        if args.delay:
            events.append(make_event('wait', args.delay))
        events += events2
        save(args.outfile, events, args.overwrite)

    elif args.command in ('length', 'len'):
        events = load(args.file)
        print(macro_length(events))

    elif args.command == 'slice':
        events = load(args.file)
        newevents = macro_slice(events, args.starttime, args.endtime)
        save(args.outfile, newevents, args.overwrite)

    elif args.command in ('speedup', 'speed'):
        events = load(args.file)
        newevents = macro_speedup(events, args.speed)
        save(args.outfile, newevents, args.overwrite)
