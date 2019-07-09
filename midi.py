import struct
import enum
import re
import atexit
try:
    import pygame as pg
    import pygame.midi
except:
    pass

class HexInt(int):
    def __repr__(self):
        return hex(self)
    def __str__(self):
        return repr(self)

class MidiStatusByte(int):
    @property
    def status(self):
        return MidiStatus(self & 0xf0)
    @property
    def channel(self):
        return self & 0x0f
    def __repr__(self):
        return f'<{self.status.name}|{self.channel}: {self:#x}>'
    def __str__(self):
        return repr(self)

class MidiStatus(HexInt, enum.Enum):
    NoteOff    = 0x80
    NoteOn     = 0x90
    KeyPress   = 0xA0
    CtrlChange = 0xB0
    ProgChange = 0xC0
    ChannPress = 0xD0
    PitchBend  = 0xE0
    NonMidi    = 0xF0

globals().update(MidiStatus.__members__)

class MetaEvent(HexInt, enum.Enum):
    SeqNumber = 0x00
    TextEvent = 0x01
    Copyright = 0x02
    TrackName = 0x03
    InstrName = 0x04
    Lyric     = 0x05
    Marker    = 0x06
    CuePoint  = 0x07
    ChannPref = 0x20
    EndOfTrk  = 0x2f
    SetTempo  = 0x51
    SMTPEOff  = 0x54
    TimeSig   = 0x58
    KeySig    = 0x59
    Specific  = 0x7f

N_DATA_BYTES = {
    NoteOff: 2, NoteOn: 2, KeyPress: 2, CtrlChange: 2, ProgChange: 1,
    ChannPress: 1, PitchBend: 2,
}


def read_midi(file):
    if isinstance(file, str):
        file = open(file, 'rb')
    with file:
        buff = file.read()
    chunks = []
    chunkhead = struct.Struct('>4sI')
    headerdata = struct.Struct('>HHh')
    i = 0
    while i < len(buff):
        typ, length = chunkhead.unpack_from(buff, i)
        i += chunkhead.size
        if typ == b'MThd':
            data = fmt, trks, div = headerdata.unpack_from(buff, i)
            if div & 0x8000:
                fps = -(div & -0x100)
                tpf = div & 0xff
                data = (fmt, trks, (fps, tpf))
        elif typ == b'MTrk':
            data = parse_track_data(buff, i, length)
        else:
            data = buff[i: i+length]
        chunks.append((typ, data))
        i += length
    return chunks

def parse_track_data(data, offset=0, length=None):
    i = offset
    end = offset + length if length is not None else len(data)
    events = []
    running_status = 0
    while i < end:
        dt, i = parse_vlq(data, i)
        status = data[i]
        i += 1
        # Sysex Event
        if status in (0xf0, 0xf7):
            length, i = parse_vlq(data, i)
            edata = (HexInt(status), data[i: i+length])
            i += length
        # Meta Event
        elif status == 0xff:
            try:
                typ = MetaEvent(data[i])
            except ValueError:
                typ = HexInt(data[i])
            length, i = parse_vlq(data, i+1)
            edata = (HexInt(status), typ, data[i: i+length])
            i += length
        # MIDI Event
        else:
            # Running status
            if not status & 0x80:
                status = running_status
                i -= 1
            running_status = status
            statusb = status & 0xf0
            channel = status & 0x0f
            length = N_DATA_BYTES[statusb]
            edata = (MidiStatusByte(status), *data[i: i+length])
            i += length
        events.append((dt, edata))
    return events

def parse_vlq(data, offset=0):
    i = offset
    n = 0
    msb = 1
    while msb:
        b = data[i]
        n = n << 7 | b & 0x7f
        msb = b >> 7
        i += 1
    return n, i


def abs_events(track):
    events = []
    tick = 0
    for dt, evt in track:
        tick += dt
        events.append((evt, tick))
    return events

def merge_events(tracks):
    events = []
    for track in tracks:
        events.extend(abs_events(track))
    events.sort(key=lambda evt: evt[1])
    return events

def schedule_events(events, division, sysex=False, meta=False):
    tempo = 500_000
    if isinstance(division, int):
        ms_per_tick = tempo / (division * 1000)
    else:
        ms_per_tick = 1000 / (division[0] * division[1])
    midievents = []
    last_tick = last_ts = 0
    for evt, tick in events:
        ts = last_ts + (tick - last_tick) * ms_per_tick
        last_tick, last_ts = tick, ts
        if evt[0] == 0xff and evt[1] == MetaEvent.SetTempo:
            tempo = int.from_bytes(evt[2], 'big')
            if isinstance(division, int):
                ms_per_tick = tempo / (division * 1000)
        if (evt[0] in (0xf0, 0xf7) and sysex or
             evt[0] == 0xff and meta or
             evt[0] < 0xf0):
            midievents.append((evt, int(ts)))
    return midievents

def get_tracks(file):
    chunks = file
    if isinstance(file, str) or hasattr(file, 'read'):
        chunks = read_midi(file)
    tracks = [track for typ, track in chunks[1:]]
    division = chunks[0][1][2]
    return tracks, division

def get_raw_events(file):
    tracks, division = get_tracks(file)
    return merge_events(tracks), division

def get_midi_events(file, sysex=False, meta=False):
    return schedule_events(*get_raw_events(file), sysex=sysex, meta=meta)

##def play_midi(file):
##    events, division = get_raw_events(file)
##    tempo = 500_000
##    if isinstance(division, int):
##        ms_per_tick = tempo / (division * 1000)
##    else:
##        ms_per_tick = 1000 / (division[0] * division[1])
##    init()
##    last_tick = 0
##    last_ts = pg.midi.time()
##    for evt, tick in events:
##        ts = last_ts + (tick - last_tick) * ms_per_tick
##        last_tick, last_ts = tick, ts
##        if evt[0] == 0xff and evt[1] == MetaEvent.SetTempo:
##            tempo = int.from_bytes(evt[2], 'big')
##            if isinstance(division, int):
##                ms_per_tick = tempo / (division * 1000)
##        pg.time.delay(int(ts) - pg.midi.time())
##        if evt[0] in (0xf0, 0xf7):
##            player.write_sys_ex(0, evt[1])
##        elif evt[0] < 0xf0:
##            player.write_short(*evt)


player = None

def init():
    global player
    if player is None:
        pg.midi.init()
        player = pg.midi.Output(pg.midi.get_default_output_id(), 1)
        atexit.register(quit)

def quit():
    global player
    if player:
        player.close()
        player = None
    pg.midi.quit()


def play_midi(file=None, events=None):
    if events is None:
        events = get_midi_events(file)
    init()
    t0 = pg.midi.time()
    for evt, ts in events:
        pg.time.delay(ts + t0 - pg.midi.time())
        if evt[0] == 0xf0:
            player.write_sys_ex(0, b'\xf0' + evt[1])
        elif evt[0] == 0xf7:
            player.write_sys_ex(0, evt[1])
        elif evt[0] < 0xf0:
            player.write_short(*evt)
    pg.time.delay(500)


def play_midi2(file=None, events=None):
    if events is None:
        events = get_midi_events(file)
    init()
    t0 = pg.midi.time()
    while events:
        data = events[:1024]
        player.write([(evt, ts+t0) for evt, ts in data if evt[0] < 0xf0])
        pg.time.delay(data[-1][1] + t0 - pg.midi.time())
        events = events[1024:]
    pg.time.delay(500)


def shift(events, dt):
    return [(evt, ts+dt) for evt, ts in events]



def get_notes(file=None, events=None, off=False):
    import numpy as np
    if events is None:
        events = get_midi_events(file)
    noteon = np.array([(t, e[1]) for e, t in events
                       if e[0] & 0xf0 == NoteOn and e[2] > 0])
    if noteon.size == 0:
        return tuple(np.array([], int) for i in range(3 if off else 2))
    if not off:
        return noteon[:, 0], noteon[:, 1]
    noteoff = np.array([(t, e[1]) for e, t in events
                        if e[0] & 0xf0 == NoteOff or
                           e[0] & 0xf0 == NoteOn and e[2] == 0])
    indon = np.argsort(noteon[:, 1], kind='mergesort')
    indoff = np.argsort(noteoff[:, 1], kind='mergesort')
    noteoff[indon] = noteoff[indoff]
    return noteon[:, 0], noteoff[:, 0], noteon[:, 1]



NOTEMAP = {
    'C'   : 60,   'C#'  : 61,   'Db'  : 61,   'D'   : 62,   'D#'  : 63,
    'Eb'  : 63,   'E'   : 64,   'F'   : 65,   'F#'  : 66,   'Gb'  : 66,
    'G'   : 67,   'G#'  : 68,   'Ab'  : 68,   'A'   : 69,   'A#'  : 70,
    'Bb'  : 70,   'B'   : 71,
}

def parse_note(note):
    match = re.fullmatch(r'([A-G][#b]?)([0-9])?', note)
    if not match:
        raise ValueError(f'invalid note: {note}')
    note, num = match.groups()
    num = int(num) if num else 4
    return NOTEMAP[note] + 12*num - 48


class SimplePlayer:
    def __init__(self, instrument=0, output=None):
        if output is None:
            init()
            self._player = None
        elif isinstance(output, pg.midi.Output):
            self._player = output
        else:
            pg.midi.init()
            self._player = pg.midi.Output(output)
        self.set_instrument(instrument)

    @property
    def player(self):
        return self._player or player

    def set_instrument(self, instrument):
        self.player.set_instrument(instrument)

    def wait(self, duration=1.0):
        pg.time.delay(int(duration * 1000))

    def play_note(self, note, duration=1.0, velocity=127):
        if isinstance(note, str):
            note = parse_note(note) if note.strip() else -1
        if note is None or note < 0:
            self.wait(duration)
            return
        try:
            self.player.note_on(note, velocity)
            self.wait(duration)
        finally:
            self.player.note_off(note)

    def play_fixed_notes(self, notes, duration=0.5, delay=0.0):
        for note in notes:
            self.wait(delay)
            self.play_note(note, duration)

    def play_notes(self, notes):
        for delay, note, dur in notes:
            self.wait(delay)
            self.play_note(note, dur)

    def close(self):
        if self._player:
            self._player.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2 or '-h' in sys.argv:
        sys.exit('usage: midi.py file.mid')
    play_midi(sys.argv[1])
