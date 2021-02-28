#!/usr/bin/env python3
import sys, os, struct, enum, time, re, warnings

DEFAULT_BACKEND = 'rtmidi'
_backend = None

STATUS_MASK = 0xf0
CHANNEL_MASK = 0x0f

class MidiStatusByte(int):
    @property
    def status(self):
        return MidiStatus(self & STATUS_MASK)
    @property
    def channel(self):
        return self & CHANNEL_MASK
    def __repr__(self):
        return f'<{self.status.name}|{self.channel}: {self:#x}>'
    def __str__(self):
        return repr(self)

class HexInt(int):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)
    def __repr__(self):
        return hex(self)
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

    SysEx      = 0xF0
    SysExEsc   = 0xF7
    Meta       = 0xFF

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
            fmt, ntrks, div = headerdata.unpack_from(buffer, i)
            if div & 0x8000:
                fps = -(div >> 8)
                tpf = div & 0xff
                div = (fps, tpf)
            data = fmt, ntrks, div
        elif typ == b'MTrk':
            data = parse_track_data(buffer, i, length)
        else:
            warnings.warn(f'unknown chunk type: {typ}')
            data = buffer[i: i+length]
        if not chunks and typ != b'MThd':
            raise ValueError('failed to parse midi file: no header chunk found')
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
        if status in (SysEx, SysExEsc):
            length, i = parse_vlq(buffer, i)
            event = (MidiStatus(status), buffer[i: i+length])
            i += length
        # Meta Event
        elif status == Meta:
            try:
                typ = MetaEvent(buffer[i])
            except ValueError:
                typ = HexInt(buffer[i])
            length, i = parse_vlq(buffer, i+1)
            data = metaevent_data(typ, buffer[i: i+length])
            event = (MidiStatus(status), typ, data)
            i += length
        # MIDI Event
        else:
            # Running status
            if not status & 0x80:
                status = running_status
                i -= 1
            running_status = status
            length = N_DATA_BYTES[status & STATUS_MASK]
            event = (MidiStatusByte(status), *buffer[i: i+length])
            i += length
        events.append((event, dt))
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
    for evt, dt in track:
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
        sec_per_tick = tempo / (division * 1000_000)
    else:
        sec_per_tick = 1 / (division[0] * division[1])
    midievents = []
    last_tick = last_ts = 0
    for evt, tick in events:
        ts = last_ts + (tick - last_tick) * sec_per_tick
        last_tick, last_ts = tick, ts
        if evt[0] == Meta and evt[1] == MetaEvent.SetTempo:
            tempo = evt[2]
            if isinstance(division, int):
                sec_per_tick = tempo / (division * 1000_000)
        if (evt[0] in (SysEx, SysExEsc) and sysex or
                evt[0] == Meta and meta or
                evt[0] < NonMidi):
            midievents.append((evt, ts))
    return midievents

def get_tracks(file):
    chunks = file
    if isinstance(file, str) or hasattr(file, 'read'):
        chunks = read_midi(file)
    tracks = [track for typ, track in chunks[1:] if typ == b'MTrk']
    division = chunks[0][1][2]
    return tracks, division

def get_raw_events(file):
    tracks, division = get_tracks(file)
    return merge_events(tracks), division

def get_midi_events(file, sysex=False, meta=False):
    return schedule_events(*get_raw_events(file), sysex=sysex, meta=meta)



def shift(events, dt):
    return [(evt, ts+dt) for evt, ts in events]


def slice(events, start, end=None):
    if end is None:
        end = events[-1][1]
    return [(evt, ts-start) for evt, ts in events if start <= ts <= end]


def filter_events(events, type=None, channel=None):
    if type is not None and not isinstance(type, (list, tuple, set)):
        type = (type,)
    if channel is not None and not isinstance(channel, (list, tuple, set)):
        channel = (channel,)
    ret = []
    for evt, dt in events:
        if (type is None
             or evt[0] in type
             or (evt[0] < NonMidi and evt[0] & STATUS_MASK in type)
             or (evt[0] == Meta and evt[1] in type)):
            if (channel is None
                 or (evt[0] < NonMidi and evt[0] & CHANNEL_MASK in channel)):
                ret.append((evt, dt))
    return ret


def get_notes(file=None, events=None, off=False, ticks=False):
    import numpy as np
    if events is None:
        events = get_raw_events(file)[0] if ticks else get_midi_events(file)
    noteon = np.array([(t, e[1]) for e, t in events
                       if e[0] & STATUS_MASK == NoteOn and e[2] > 0])
    if noteon.size == 0:
        return tuple(np.array([], int) for i in range(3 if off else 2))
    if not off:
        return noteon[:, 0], noteon[:, 1]
    noteoff = np.array([(t, e[1]) for e, t in events
                        if e[0] & STATUS_MASK == NoteOff or
                           e[0] & STATUS_MASK == NoteOn and e[2] == 0])
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



NOTE_MAP = {
    'Cb': -1,  'C':  0,  'C#':  1,  'Db':  1,  'D':  2,  'D#':  3,
    'Eb':  3,  'E':  4,  'E#':  5,  'Fb':  4,  'F':  5,  'F#':  6,
    'Gb':  6,  'G':  7,  'G#':  8,  'Ab':  8,  'A':  9,  'A#': 10,
    'Bb': 10,  'B': 11,  'B#': 12,
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def parse_note(note):
    if isinstance(note, int):
        return note
    match = re.fullmatch(r'([A-Ga-g][#b♯♭]?)(-?[0-9])?', note)
    if not match:
        raise ValueError(f'invalid note: {note}')
    note, num = match.groups()
    note = note[0].upper() + note[1:].replace('♯', '#').replace('♭', 'b')
    num = int(num) if num else 4
    return NOTE_MAP[note] + 12*(num + 1)

def note_name(note):
    return NOTE_NAMES[note % 12] + str(note // 12 - 1)

def note_frequency(note):
    note = parse_note(note)
    return 440.0 * 2**((note - 69) / 12)


def major_scale(start, end):
    start = parse_note(start)
    end = parse_note(end)
    steps = [2, 2, 1, 2, 2, 2, 1]
    i = 0
    l = []
    while start <= end:
        l.append(start)
        start += steps[i]
        i = (i + 1) % 7
    return l


def pitch_bend_bytes(p):
    x = min(max(int(8192*(p+1)), 0), 16383)
    return x & 127, x >> 7


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

PERCUSSION_CHANNEL = 9


def set_backend(backend):
    global _backend
    if backend:
        assert backend in _PLAYER_CLASSES
    _backend = backend

def get_backend():
    global _backend
    if not _backend:
        _backend = os.environ.get('MIDI_BACKEND', DEFAULT_BACKEND)
        if _backend == 'rtmidi':
            try:
                import rtmidi
            except ImportError:
                warnings.warn("Couldn't load rtmidi backend. Falling back to pygame.")
                _backend = 'pygame'
        elif _backend != 'pygame':
            raise ValueError(f'Unknown backend: {_backend}')
    return _backend

def get_player_class():
    return _PLAYER_CLASSES[get_backend()]


class MidiPlayer:
    def __new__(cls, output=None, instrument=None):
        if cls is MidiPlayer:
            cls = get_player_class()
        return super().__new__(cls)

    def __init__(self, output=None, instrument=None):
        if instrument is not None:
            try:
                self.set_instrument(instrument)
            except:
                self.close()
                raise

    def send_message(self, message):
        raise NotImplementedError

    def send_sysex(self, message):
        self.send_message(message)

    def note_on(self, note, velocity=127, channel=0):
        self.send_message([NoteOn + channel, parse_note(note), velocity])

    def note_off(self, note, velocity=0, channel=0):
        self.send_message([NoteOff + channel, parse_note(note), velocity])

    def all_notes_off(self, channel=None):
        channels = [channel] if channel is not None else range(16)
        for ch in channels:
            # Channel Mode 120: All Sound Off
            self.send_message([CtrlChange, 120, 0])
            # Fallback
            for note in range(128):
                self.note_off(note, channel=ch)

    def set_instrument(self, instrument, channel=0):
        if isinstance(instrument, str):
            instrument = INSTRUMENTS[instrument.lower()]
        self.send_message([ProgChange + channel, instrument])

    def wait(self, duration=1.0):
        if duration > 0:
            time.sleep(duration)

    def time(self):
        return time.monotonic()

    def play_midi(self, file=None, events=None, volume=1, tempo_scale=1,
                  start=0, sysex=False, print_progress=True):
        if events is None:
            events = get_midi_events(file, sysex=True, meta=True)
        tottime = events[-1][1] / tempo_scale
        last_ts = 0
        notes_on = set()
        try:
            t0 = self.time() - start
            for evt, ts in events:
                ts /= tempo_scale
                if ts < start and evt[0] & STATUS_MASK in (NoteOn, NoteOff):
                    continue
                # Print before waiting to hide delay
                if print_progress and last_ts != ts and last_ts >= start:
                    print(f'\r{fmt_time(last_ts)}/{fmt_time(tottime)}', end='')
                self.wait(ts + t0 - self.time())
                if sysex and evt[0] == SysEx:
                    self.send_sysex(b'\xf0' + evt[1])
                elif sysex and evt[0] == SysExEsc:
                    self.send_sysex(evt[1])
                elif evt[0] < NonMidi:
                    if evt[0] & STATUS_MASK == NoteOn:
                        if volume != 1:
                            evt = (evt[0], evt[1], min(int(evt[2]*volume), 127))
                        notes_on.add((evt[0] & CHANNEL_MASK, evt[1]))
                    elif evt[0] & STATUS_MASK == NoteOff:
                        notes_on.discard((evt[0] & CHANNEL_MASK, evt[1]))
                    self.send_message(bytes(evt))
                last_ts = ts
            self.wait(.5)
        except KeyboardInterrupt:
            for ch, note in notes_on:
                self.note_off(note, channel=ch)
        if print_progress:
            print(f'\r{fmt_time(last_ts)}/{fmt_time(tottime)}')

    def play_note(self, note, duration=1.0, velocity=127, channel=0,
                  instrument=None):
        if instrument is not None:
            self.set_instrument(instrument, channel)
        if isinstance(note, str):
            note = parse_note(note) if note.strip() else -1
        if note is None or note < 0:
            self.wait(duration)
            return
        try:
            self.note_on(note, velocity, channel)
            self.wait(duration)
        finally:
            self.note_off(note, channel=channel)

    def play_notes(self, notes, duration=0.5, delay=0.0, velocity=127,
                   channel=0, instrument=None):
        if instrument is not None:
            self.set_instrument(instrument, channel)
        for note in notes:
            dur, dely = duration, delay
            if isinstance(note, tuple):
                if len(note) == 1:
                    note, = note
                elif len(note) == 2:
                    note, dur = note
                else:
                    dely, note, dur = note
            self.wait(dely)
            self.play_note(note, dur, velocity, channel)

    def close(self):
        pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RtMidiPlayer(MidiPlayer):
    def __init__(self, output=None, instrument=None):
        import rtmidi
        self.output = rtmidi.MidiOut()
        self.output.open_port(output or 0)
        super().__init__(output, instrument)

    @staticmethod
    def list_outputs():
        import rtmidi
        output = rtmidi.MidiOut()
        return output.get_ports()

    def send_message(self, message):
        self.output.send_message(message)

    def close(self):
        if hasattr(self, 'output'):
            self.output.close_port()
            del self.output


class PygameMidiPlayer(MidiPlayer):
    def __init__(self, output=None, instrument=None):
        global pygame
        import pygame.midi
        pygame.midi.init()
        if output is None:
            output = pygame.midi.get_default_output_id()
        self.output = pygame.midi.Output(output)
        super().__init__(output, instrument)

    @staticmethod
    def list_outputs():
        import pygame.midi
        pygame.midi.init()
        infos = []
        for i in range(pygame.midi.get_count()):
            di = pygame.midi.get_device_info(i)
            if di[3]:
                infos.append(di[1].decode())
        return infos

    def send_message(self, message):
        self.output.write_short(*message)

    def send_sysex(self, message):
        self.output.write_sys_ex(0, message)

    def wait(self, duration=1.0):
        pygame.time.delay(int(duration * 1000))

    def time(self):
        return pygame.midi.time() / 1000

    def close(self):
        if hasattr(self, 'output'):
            self.output.close()
            del self.output


_PLAYER_CLASSES = {'rtmidi': RtMidiPlayer, 'pygame': PygameMidiPlayer}



def fmt_time(time):
    m, s = divmod(int(time), 60)
    return f'{m}:{s:02}'


def parse_time(string):
    if ':' in string:
        m, s = string.split(':')
        return int(m)*60 + float(s)
    return float(string)


def play_midi(file=None, events=None, volume=1, tempo_scale=1, start=0,
              sysex=False, print_progress=True, output=None):
    with MidiPlayer(output) as player:
        player.play_midi(
            file, events, volume, tempo_scale, start, sysex, print_progress)


def play_notes(notes, duration=0.5, delay=0.0, velocity=127, channel=0,
               instrument=None, output=None):
    with MidiPlayer(output) as player:
        player.play_notes(notes, duration, delay, velocity, channel, instrument)


def all_notes_off(output=None):
    with MidiPlayer(output) as player:
        player.all_notes_off()


def list_outputs():
    return get_player_class().list_outputs()


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('file', nargs='?')
    p.add_argument('-v', '--volume', type=float, default=1.0)
    p.add_argument('-t', '--tempo-scale', type=float, default=1.0)
    p.add_argument('-s', '--start', type=parse_time, default=0)
    p.add_argument('-p', '--progress', action='store_true', default=True, help='(default)')
    p.add_argument('-P', '--no-progress', dest='progress', action='store_false')
    p.add_argument('-S', '--sysex', action='store_true')
    p.add_argument('-o', '--output', type=int)
    p.add_argument('-b', '--backend')
    p.add_argument('-L', '--length', action='store_true')
    p.add_argument('-A', '--all-notes-off', action='store_true')
    p.add_argument('-l', '--list-outputs', action='store_true')
    args = p.parse_args()
    set_backend(args.backend)
    if args.list_outputs:
        for o in list_outputs():
            print(o)
        return
    if args.all_notes_off:
        all_notes_off(args.output)
        return
    if not args.file:
        p.error('midi file is required')
    if args.length:
        events = get_midi_events(args.file)
        print(fmt_time(events[-1][1]))
    else:
        play_midi(
            args.file, volume=args.volume, tempo_scale=args.tempo_scale,
            start=args.start, sysex=args.sysex, print_progress=args.progress,
            output=args.output)

if __name__ == '__main__':
    main()
