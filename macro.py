import time, pymouse, pykeyboard, json

class MouseRecorder(pymouse.PyMouseEvent):
    def __init__(self, track_movement=True):
        super().__init__()
        self.events = []
        self.track_movement = track_movement

    def run(self):
        self.time = time.time()
        super().run()

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

recorder = None

def record(track_movement=True):
    global recorder
    recorder = MouseRecorder(track_movement)
    recorder.start()

def stop():
    global recorder
    recorder.stop()

def save(file, events=None):
    if isinstance(file, str):
        file = open(file, 'w')
    if events is None:
        events = recorder.events
    with file:
        json.dump(events, file)

def load(file):
    if isinstance(file, str):
        file = open(file, 'w')
    with file:
        data = json.load(file)
        recorder.events = data
        return data

def playback(events=None, speed=1.0):
    global recorder
    if events is None:
        events = recorder.events
    mouse = pymouse.PyMouse()
    escaper = pykeyboard.PyKeyboardEvent()
    escaper.start()
    for event in recorder.events:
        # keyboard event stops on escape key
        if not escaper.is_alive():
            break
        type, dtime, x, y, *rest = event
        time.sleep(dtime / speed)
        if type == 'click':
            button, press = rest
            if press:
                mouse.press(x, y, button)
            else:
                mouse.release(x, y, button)
        elif type == 'move':
            mouse.move(x, y)
