#!/usr/bin/env python3.7
import struct
import enum
import re
import atexit
try:
    import pygame as pg
    import pygame.midi
except ImportError:
    pass

class HexInt(int):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)
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
    ProgName  = 0x08
    DevName   = 0x09
    ChannPref = 0x20
    MIDIPort  = 0x21
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
        with open(file, 'rb') as file:
            buffer = file.read()
    else:
        buffer = file.read()
    chunks = []
    chunkhead = struct.Struct('>4sI')
    headerdata = struct.Struct('>HHh')
    i = 0
    while i < len(buffer):
        typ, length = chunkhead.unpack_from(buffer, i)
        i += chunkhead.size
        if typ == b'MThd':
            data = fmt, trks, div = headerdata.unpack_from(buffer, i)
            if div & 0x8000:
                fps = -(div >> 8)
                tpf = div & 0xff
                data = (fmt, trks, (fps, tpf))
        elif typ == b'MTrk':
            data = parse_track_data(buffer, i, length)
        else:
            data = buffer[i: i+length]
        if not chunks and typ != b'MThd':
            raise ValueError('Invalid midi file')
        chunks.append((typ, data))
        i += length
    return chunks

def parse_track_data(buffer, offset=0, length=None):
    i = offset
    end = offset + length if length is not None else len(buffer)
    events = []
    running_status = 0
    while i < end:
        dt, i = parse_vlq(buffer, i)
        status = buffer[i]
        i += 1
        # Sysex Event
        if status in (0xf0, 0xf7):
            length, i = parse_vlq(buffer, i)
            event = (HexInt(status), buffer[i: i+length])
            i += length
        # Meta Event
        elif status == 0xff:
            try:
                typ = MetaEvent(buffer[i])
            except ValueError:
                typ = HexInt(buffer[i])
            length, i = parse_vlq(buffer, i+1)
            data = metaevent_data(typ, buffer[i: i+length])
            event = (HexInt(status), typ, data)
            i += length
        # MIDI Event
        else:
            # Running status
            if not status & 0x80:
                status = running_status
                i -= 1
            running_status = status
            length = N_DATA_BYTES[status & 0xf0]
            event = (MidiStatusByte(status), *buffer[i: i+length])
            i += length
        events.append((dt, event))
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

def metaevent_data(typ, data):
    if typ in {MetaEvent.SeqNumber, MetaEvent.ChannPref,
                MetaEvent.MIDIPort, MetaEvent.SetTempo}:
        data = int.from_bytes(data, 'big')
    elif typ == MetaEvent.SMTPEOff:
        data = tuple(data)
    elif typ == MetaEvent.TimeSig:
        data = data[0], 2**data[1], data[2], data[3]
    elif typ == MetaEvent.KeySig:
        data = struct.unpack('bB', data)
    elif typ == MetaEvent.EndOfTrk:
        data = None
    return data


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
            tempo = evt[2]
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
##            tempo = evt[2]
##            if isinstance(division, int):
##                ms_per_tick = tempo / (division * 1000)
##        pg.time.delay(int(ts) - pg.midi.time())
##        if evt[0] in (0xf0, 0xf7):
##            player.write_sys_ex(0, evt[1])
##        elif evt[0] < 0xf0:
##            player.write_short(*evt)


player = None

def init(output=None):
    global player
    if player is None:
        pg.midi.init()
        if output is None:
            output = pg.midi.get_default_output_id()
        player = pg.midi.Output(output, 1)
        atexit.register(quit)

def quit():
    global player
    if player:
        player.close()
        player = None
    pg.midi.quit()


def play_midi(file=None, events=None, volume=1, start=0, print_progress=True):
    if events is None:
        events = get_midi_events(file, sysex=True, meta=True)
    init()
    tottime = events[-1][1]
    last_ts = 0
    try:
        t0 = pg.midi.time() - start
        for evt, ts in events:
            if ts < start:
                continue
            if print_progress and last_ts != ts:
                print(f'\r{fmt_time(last_ts)}/{fmt_time(tottime)}', end='')
            pg.time.delay(ts + t0 - pg.midi.time())
            if evt[0] == 0xf0:
                player.write_sys_ex(0, b'\xf0' + evt[1])
            elif evt[0] == 0xf7:
                player.write_sys_ex(0, evt[1])
            elif evt[0] < 0xf0:
                if volume != 1 and evt[0] & 0xf0 == NoteOn:
                    evt = (evt[0], evt[1], min(int(evt[2]*volume), 127))
                player.write_short(*evt)
            last_ts = ts
        pg.time.wait(500)
    except KeyboardInterrupt:
        pass
    if print_progress:
        print(f'\r{fmt_time(last_ts)}/{fmt_time(tottime)}')


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


def slice(events, start, end=None):
    if end is None:
        end = events[-1][1]
    return [(evt, ts-start) for evt, ts in events if start <= ts <= end]



def get_notes(file=None, events=None, off=False, ticks=False):
    import numpy as np
    if events is None:
        events = get_raw_events(file)[0] if ticks else get_midi_events(file)
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


def get_notes_mido(midofile=None, off=False, ticks=False):
    import numpy as np
    import mido
    msgs = mido.merge_tracks(midofile.tracks) if ticks else list(midofile)
    msgs = list(mido.midifiles.tracks._to_abstime(msgs))
    noteon = np.array([(m.time, m.note) for m in msgs
                       if m.type == 'note_on' and m.velocity > 0])
    if noteon.size == 0:
        return tuple(np.array([], int) for i in range(3 if off else 2))
    if not off:
        return noteon[:, 0], noteon[:, 1]
    noteoff = np.array([(m.time, m.note) for m in msgs
                        if m.type == 'note_off' or
                           m.type == 'note_on' and m.velocity == 0])
    indon = np.argsort(noteon[:, 1], kind='mergesort')
    indoff = np.argsort(noteoff[:, 1], kind='mergesort')
    noteoff[indon] = noteoff[indoff]
    return noteon[:, 0], noteoff[:, 0], noteon[:, 1]



NOTEMAP = {
    'Cb': 59,  'C' : 60,  'C#': 61,  'Db': 61,  'D' : 62,  'D#': 63,
    'Eb': 63,  'E' : 64,  'E#': 65,  'Fb': 64,  'F' : 65,  'F#': 66,
    'Gb': 66,  'G' : 67,  'G#': 68,  'Ab': 68,  'A' : 69,  'A#': 70,
    'Bb': 70,  'B' : 71,  'B#': 72,
}

def parse_note(note):
    match = re.fullmatch(r'([A-G][#b]?)([0-9])?', note)
    if not match:
        raise ValueError(f'invalid note: {note}')
    note, num = match.groups()
    num = int(num) if num else 4
    return NOTEMAP[note] + 12*(num - 4)


INSTRUMENT_NAMES = [
# Piano
'Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano',
'Honky-tonk Piano', 'Electric Piano 1', 'Electric Piano 2', 'Harpsichord',
'Clavinet',
# Chromatic Percussion
'Celesta', 'Glockenspiel', 'Music Box', 'Vibraphone', 'Marimba', 'Xylophone',
'Tubular Bells', 'Dulcimer',
# Organ
'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ', 'Reed Organ',
'Accordion', 'Harmonica', 'Tango Accordion',
# Guitar
'Acoustic Guitar (nylon)', 'Acoustic Guitar (steel)', 'Electric Guitar (jazz)',
'Electric Guitar (clean)', 'Electric Guitar (muted)', 'Overdriven Guitar',
'Distortion Guitar', 'Guitar harmonics',
# Bass
'Acoustic Bass', 'Electric Bass (finger)', 'Electric Bass (pick)',
'Fretless Bass', 'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1', 'Synth Bass 2',
# Strings
'Violin', 'Viola', 'Cello', 'Contrabass', 'Tremolo Strings',
'Pizzicato Strings', 'Orchestral Harp', 'Timpani',
# Ensemble
'String Ensemble 1', 'String Ensemble 2', 'Synth Strings 1', 'Synth Strings 2',
'Choir Aahs', 'Voice Oohs', 'Synth Voice', 'Orchestra Hit',
# Brass
'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet', 'French Horn', 'Brass Section',
'Synth Brass 1', 'Synth Brass 2',
# Reed
'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax', 'Oboe', 'English Horn',
'Bassoon', 'Clarinet',
# Pipe
'Piccolo', 'Flute', 'Recorder', 'Pan Flute', 'Blown Bottle', 'Shakuhachi',
'Whistle', 'Ocarina',
# Synth Lead
'Lead 1 (square)', 'Lead 2 (sawtooth)', 'Lead 3 (calliope)', 'Lead 4 (chiff)',
'Lead 5 (charang)', 'Lead 6 (voice)', 'Lead 7 (fifths)', 'Lead 8 (bass + lead)',
# Synth Pad
'Pad 1 (new age)', 'Pad 2 (warm)', 'Pad 3 (polysynth)', 'Pad 4 (choir)',
'Pad 5 (bowed)', 'Pad 6 (metallic)', 'Pad 7 (halo)', 'Pad 8 (sweep)',
# Synth Effects
'FX 1 (rain)', 'FX 2 (soundtrack)', 'FX 3 (crystal)', 'FX 4 (atmosphere)',
'FX 5 (brightness)', 'FX 6 (goblins)', 'FX 7 (echoes)', 'FX 8 (sci-fi)',
# Ethnic
'Sitar', 'Banjo', 'Shamisen', 'Koto', 'Kalimba', 'Bag pipe', 'Fiddle', 'Shanai',
# Percussive
'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock', 'Taiko Drum', 'Melodic Tom',
'Synth Drum', 'Reverse Cymbal',
# Sound Effects
'Guitar Fret Noise', 'Breath Noise', 'Seashore', 'Bird Tweet', 'Telephone Ring',
'Helicopter', 'Applause', 'Gunshot']

INSTRUMENTS = {k.lower(): i for i, k in enumerate(INSTRUMENT_NAMES)}


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
        if isinstance(instrument, str):
            instrument = INSTRUMENTS[instrument.lower()]
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


def fmt_time(time):
    m, s = divmod(time // 1000, 60)
    return f'{m}:{s:02}'


def parse_time(string):
    if ':' in string:
        m, s = string.split(':')
        return int((int(m)*60 + float(s))*1000)
    return int(float(string)*1000)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('file')
    p.add_argument('-v', '--volume', type=float, default=1.0)
    p.add_argument('-l', '--length', action='store_true')
    p.add_argument('-s', '--start', type=parse_time, default=0)
    p.add_argument('-p', '--progress', action='store_true', default=True)
    p.add_argument('-P', '--no-progress', dest='progress', action='store_false')
    args = p.parse_args()
    if args.length:
        events = get_midi_events(args.file)
        print(fmt_time(events[-1][1]))
    else:
        play_midi(args.file, volume=args.volume, start=args.start,
                  print_progress=args.progress)
