#!/usr/bin/env python3
import sys, os, struct, enum, time, re, math, collections, warnings
import numpy as np

#######################
# Midi File Constants #
#######################

STATUS_MASK = 0xf0
CHANNEL_MASK = 0x0f

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

NoteOff = MidiStatus.NoteOff
NoteOn = MidiStatus.NoteOn
KeyPress = MidiStatus.KeyPress
CtrlChange = MidiStatus.CtrlChange
ProgChange = MidiStatus.ProgChange
ChannPress = MidiStatus.ChannPress
PitchBend = MidiStatus.PitchBend
SysEx = MidiStatus.SysEx
SysExEsc = MidiStatus.SysExEsc
Meta = MidiStatus.Meta
NonMidi = MidiStatus.NonMidi

MIDI_EVENTS = {s for s in MidiStatus if s < NonMidi}

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
    SMPTEOff  = 0x54
    TimeSig   = 0x58
    KeySig    = 0x59
    SecSpecif = 0x7f

N_DATA_BYTES = {
    NoteOff: 2, NoteOn: 2, KeyPress: 2, CtrlChange: 2, ProgChange: 1,
    ChannPress: 1, PitchBend: 2,
}


DEFAULT_TEMPO = 500_000


############################
# Midi File Classes/Parser #
############################

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

class RelMidiEvents(list):
    def __repr__(self):
        return f'RelMidiEvents({super().__repr__()})'

    def to_abs(self):
        events = AbsMidiEvents()
        tick = 0
        for evt, dt in self:
            tick += dt
            events.append((evt, tick))
        return events

class AbsMidiEvents(list):
    def __repr__(self):
        return f'AbsMidiEvents({super().__repr__()})'

    def to_rel(self):
        events = RelMidiEvents()
        lasttick = 0
        for evt, tick in self:
            events.append((evt, tick - lasttick))
            lasttick = tick
        return events

class ScheduledMidiEvents(list):
    def __repr__(self):
        return f'ScheduledMidiEvents({super().__repr__()})'

SmpteDivision = collections.namedtuple('SmpteDivision', ['fps', 'tpf'])


class MidiFile:
    def __init__(self, file_or_tracks, division=480, format=1):
        if isinstance(file_or_tracks, list):
            self.tracks = [RelMidiEvents(track) for track in file_or_tracks]
            self.division = division
            self.format = format
        else:
            self._read(file_or_tracks)

    def __repr__(self):
        return (f'<MidiFile ntracks={len(self.tracks)} '
                f'division={self.division} format={self.format}>')

    def merged_events(self):
        events = AbsMidiEvents()
        for track in self.tracks:
            events.extend(track.to_abs())
        events.sort(key=lambda evt: evt[1])
        return events

    def tick_duration(self, tempo):
        if isinstance(self.division, SmpteDivision):
            return 1 / (self.division.fps * self.division.tpf)
        else:
            return tempo / (self.division * 1000_000)

    def schedule_events(self, sysex=False, meta=False):
        tempo = DEFAULT_TEMPO
        sec_per_tick = self.tick_duration(tempo)
        midievents = ScheduledMidiEvents()
        last_tick = last_ts = 0
        for evt, tick in self.merged_events():
            ts = last_ts + (tick - last_tick) * sec_per_tick
            last_tick, last_ts = tick, ts
            if evt[0] == Meta and evt[1] == MetaEvent.SetTempo:
                tempo = evt[2]
                sec_per_tick = self.tick_duration(tempo)
            if (evt[0] in (SysEx, SysExEsc) and sysex or
                    evt[0] == Meta and meta or
                    evt[0] < NonMidi):
                midievents.append((evt, ts))
        return midievents

    def _read(self, file):
        if isinstance(file, str):
            with open(file, 'rb') as file:
                buffer = file.read()
        else:
            buffer = file.read()

        self.tracks = []
        self.format = self.division = ntracks = None

        if len(buffer) == 0:
            raise ValueError('failed to parse midi file: file is empty')

        chunk_head_fmt = struct.Struct('>4sI')
        header_data_fmt = struct.Struct('>HHh')
        i = 0
        while i < len(buffer):
            typ, length = chunk_head_fmt.unpack_from(buffer, i)
            i += chunk_head_fmt.size
            if typ == b'MThd':
                if self.format is not None:
                    raise ValueError('failed to parse midi file: multiple header chunks found')
                fmt, ntracks, div = header_data_fmt.unpack_from(buffer, i)
                if div & 0x8000:
                    div = SmpteDivision(-(div >> 8), div & 0xff)
                self.format, self.division = fmt, div
            elif self.format is None:
                raise ValueError('failed to parse midi file: no header chunk found')
            elif typ == b'MTrk':
                self.tracks.append(parse_track_data(buffer, i, length))
            else:
                warnings.warn(f'unknown chunk type: {typ}')
            i += length

        if len(self.tracks) != ntracks:
            warnings.warn(f'found {len(self.tracks)} tracks, expected {ntracks}')

def _as_midi_file(file):
    if isinstance(file, MidiFile):
        return file
    return MidiFile(file)


def parse_track_data(buffer, offset=0, length=None):
    i = offset
    end = offset + length if length is not None else len(buffer)
    events = RelMidiEvents()
    running_status = None
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
                assert running_status, 'invalid running status'
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
    elif typ == MetaEvent.SMPTEOff:
        data = tuple(data)
    elif typ == MetaEvent.TimeSig:
        data = data[0], 2**data[1], data[2], data[3]
    elif typ == MetaEvent.KeySig:
        data = struct.unpack('bB', data)
    elif typ == MetaEvent.EndOfTrk:
        data = None
    return data


########################
# Midi Event Utilities #
########################

def get_status(evt):
    return evt[0] & STATUS_MASK

def get_channel(evt):
    return evt[0] & CHANNEL_MASK

def is_note_on(evt):
    return get_status(evt) == NoteOn and evt[2] > 0

def is_note_off(evt):
    status = get_status(evt)
    return status == NoteOff or (status == NoteOn and evt[2] == 0)


def shift(events, dt):
    return [(evt, ts+dt) for evt, ts in events]


def slice(events, start, end=None):
    if end is None:
        end = events[-1][1]
    return [(evt, ts-start) for evt, ts in events if start <= ts <= end]


def filter_events(events, type=None, channel=None, *, note_on=False,
                  note_off=False):
    if type is not None and not isinstance(type, (list, tuple, set)):
        type = (type,)
    if type is None and (note_on or note_off):
        type = ()
    if channel is not None and not isinstance(channel, (list, tuple, set)):
        channel = (channel,)
    ret = []
    for evt, dt in events:
        if (type is None
             or evt[0] in type
             or (evt[0] < NonMidi and get_status(evt) in type)
             or (evt[0] == Meta and evt[1] in type)
             or (note_on and is_note_on(evt))
             or (note_off and is_note_off(evt))):
            if (channel is None
                 or (evt[0] < NonMidi and get_channel(evt) in channel)):
                ret.append((evt, dt))
    return ret


def get_notes(file=None, events=None, off=False, ticks=False):
    if events is None:
        file = _as_midi_file(file)
        events = file.merged_events() if ticks else file.schedule_events()
    noteon = np.array([(t, e[1]) for e, t in events if is_note_on(e)])
    if noteon.size == 0:
        return tuple(np.array([], int) for i in range(3 if off else 2))
    if not off:
        return noteon[:, 0], noteon[:, 1]
    noteoff = np.array([(t, e[1]) for e, t in events if is_note_off(e)])
    indon = np.argsort(noteon[:, 1], kind='mergesort')
    indoff = np.argsort(noteoff[:, 1], kind='mergesort')
    noteoff[indon] = noteoff[indoff]
    return noteon[:, 0], noteoff[:, 0], noteon[:, 1]


def get_notes_mido(midofile=None, off=False, ticks=False):
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


#########################
# Midi Player Utilities #
#########################

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
    if isinstance(note, str):
        note = parse_note(note)
    return 440.0 * 2**((note - 69) / 12)

def frequency_to_note(freq):
    if isinstance(freq, np.ndarray):
        return (np.round(np.log(freq / 440.0) * 12) + 69).astype(int)
    return round(math.log2(freq / 440.0) * 12) + 69


def tempo_to_bpm(tempo):
    return 1000_000 * 60 / tempo

def tempo_from_bpm(bpm):
    return 1000_000 * 60 / bpm


def scale(start, end, intervals):
    start = parse_note(start)
    end = parse_note(end)
    forward = start <= end
    if not forward:
        intervals = [-x for x in intervals[::-1]]
    i = 0
    notes = []
    while start <= end if forward else start >= end:
        notes.append(start)
        start += intervals[i]
        i = (i + 1) % len(intervals)
    return notes

MAJOR_SCALE = [2, 2, 1, 2, 2, 2, 1]
NATURAL_MINOR_SCALE = [2, 1, 2, 2, 1, 2, 2]
HARMONIC_MINOR_SCALE = [2, 1, 2, 2, 1, 3, 1]

def major_scale(start, end):
    return scale(start, end, MAJOR_SCALE)

def natural_minor_scale(start, end):
    return scale(start, end, NATURAL_MINOR_SCALE)

def harmonic_minor_scale(start, end):
    return scale(start, end, HARMONIC_MINOR_SCALE)


def pitch_bend_bytes(p):
    if isinstance(p, float):
        p = round(p * 8192)
    x = min(max(p + 8192, 0), 16383)
    return x & 127, x >> 7

def pitch_bend_value(lowb, highb):
    x = highb << 7 | lowb
    return x - 8192

def pitch_bend_float(lowb, highb):
    return pitch_bend_value(lowb, highb) / 8192


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

NON_PERC_CHANNELS = set(range(16)) - {PERCUSSION_CHANNEL}


###############
# Midi Player #
###############

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

    def pitch_bend(self, bend, channel=0):
        self.send_message([PitchBend + channel, *pitch_bend_bytes(bend)])

    def all_notes_off(self, channel=None, fallback=True):
        channels = [channel] if channel is not None else range(16)
        for ch in channels:
            # Channel Mode 120: All Sound Off
            self.send_message([CtrlChange + ch, 120, 0])
            if fallback:
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
        return time.perf_counter()

    def play_midi(self, file=None, events=None, volume=1, tempo_scale=1,
                  start=0, loop=False, sysex=False, print_progress=True,
                  print_events=False):
        if events is None:
            events = _as_midi_file(file).schedule_events(sysex=True, meta=True)
        if print_events:
            print_progress = False
        tottime = events[-1][1] / tempo_scale
        notes_on = set()
        try:
            do_loop = True
            while do_loop:
                last_ts = 0
                t0 = self.time() - start
                for evt, ts in events:
                    ts /= tempo_scale
                    if ts < start and get_status(evt) in (NoteOn, NoteOff):
                        continue
                    # Print before waiting to hide delay
                    if print_progress and last_ts != ts and last_ts >= start:
                        print(f'\r{fmt_time(last_ts)}/{fmt_time(tottime)}', end='', flush=True)
                    elif print_events:
                        print(evt)
                    self.wait(ts + t0 - self.time())
                    if sysex and evt[0] == SysEx:
                        self.send_sysex(b'\xf0' + evt[1])
                    elif sysex and evt[0] == SysExEsc:
                        self.send_sysex(evt[1])
                    elif evt[0] < NonMidi:
                        if is_note_on(evt):
                            if volume != 1:
                                evt = (evt[0], evt[1], min(int(evt[2]*volume), 127))
                            notes_on.add((get_channel(evt), evt[1]))
                        elif is_note_off(evt):
                            notes_on.discard((get_channel(evt), evt[1]))
                        self.send_message(bytes(evt))
                    last_ts = ts
                do_loop = loop
                start=0
            self.wait(.5)
        except KeyboardInterrupt:
            pass
        finally:
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
                   time_scale=1.0, channel=0, instrument=None):
        if instrument is not None:
            self.set_instrument(instrument, channel)
        for note in notes:
            note_dur, note_del = duration, delay
            if isinstance(note, tuple):
                if len(note) == 1:
                    note, = note
                elif len(note) == 2:
                    note, note_dur = note
                else:
                    note_del, note, note_dur = note
            self.wait(note_del * time_scale)
            self.play_note(note, note_dur * time_scale, velocity, channel)

    def close(self):
        pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


#################
# Midi Backends #
#################

_backend = None

DEFAULT_BACKEND = 'rtmidi'

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


class RtMidiPlayer(MidiPlayer):
    def __init__(self, output=None, instrument=None):
        import rtmidi
        if isinstance(output, rtmidi.MidiOut):
            self.output = output
        else:
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
        if isinstance(output, pygame.midi.Output):
            self.output = output
        else:
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
            devinfo = pygame.midi.get_device_info(i)
            if devinfo[3]:
                infos.append(try_decode(devinfo[1]))
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
            try:
                self.output.close()
            except:
                pass
            del self.output


_PLAYER_CLASSES = {'rtmidi': RtMidiPlayer, 'pygame': PygameMidiPlayer}


##################
# Misc Utilities #
##################

def fmt_time(time):
    m, s = divmod(int(time), 60)
    return f'{m}:{s:02}'


def parse_time(string):
    if ':' in string:
        m, s = string.split(':')
        return int(m)*60 + float(s)
    return float(string)


def play_midi(file=None, events=None, volume=1, tempo_scale=1, start=0,
              loop=False, sysex=False, print_progress=True, print_events=False,
              output=None):
    with MidiPlayer(output) as player:
        player.play_midi(
            file=file, events=events, volume=volume, tempo_scale=tempo_scale,
            start=start, loop=loop, sysex=sysex, print_progress=print_progress,
            print_events=print_events)


def play_notes(notes, duration=0.5, delay=0.0, velocity=127, time_scale=1,
               channel=0, instrument=None, output=None):
    with MidiPlayer(output) as player:
        player.play_notes(notes, duration, delay, velocity, time_scale,
                          channel, instrument)
        player.wait(.5)


def all_notes_off(output=None):
    with MidiPlayer(output) as player:
        player.all_notes_off(fallback=True)


def list_outputs():
    return get_player_class().list_outputs()


def try_decode(bts):
    try:
        return bts.decode('utf-8')
    except UnicodeDecodeError:
        return bts.decode('cp1252', 'replace')


def dump_info(mf: MidiFile):
    events = mf.schedule_events(meta=True)
    time = fmt_time(events[-1][1])
    tempo_evts = filter_events(events, MetaEvent.SetTempo)
    tempos = {e[2] for e, _ in tempo_evts} or [DEFAULT_TEMPO]
    tempos_bpm = sorted(map(tempo_to_bpm, tempos))
    tempo_fmt = '/'.join(str(round(t)) for t in tempos_bpm[:3])
    tempo_fmt += '…' * (len(tempos_bpm) > 3)
    nnotes = len(filter_events(events, note_on=True))
    format_fmt = f'format: {mf.format}, ' if mf.format != 1 else ''
    print(f'# Tracks: {len(mf.tracks)}, {format_fmt}duration: {time}, division: {mf.division}, '
          f'tempo: {tempo_fmt} bpm, notes: {nnotes}, events: {len(events)}')

    for i, track in enumerate(mf.tracks):
        name = ''
        if name_evts := filter_events(track, MetaEvent.TrackName):
            name = try_decode(name_evts[0][0][2].rstrip(b'\0'))
        notes = filter_events(track, note_on=True)
        channels = {get_channel(e) for e, _ in notes}
        instrs = []
        if PERCUSSION_CHANNEL in channels:
            instrs.append('Percussion')
        if prog_evts := filter_events(track, ProgChange, NON_PERC_CHANNELS):
            instrs.extend({INSTRUMENT_NAMES[e[1]]: None for e, _ in prog_evts})
        instr_lbl = ', '.join(instrs)
        nnotes = len(notes)

        name_fmt = name and f' ({name})'
        instr_fmt = instr_lbl and f'{instr_lbl}, '
        print(f'Track {i+1}{name_fmt}: {instr_fmt}{nnotes} notes, {len(track)} events')


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('file', nargs='?')
    p.add_argument('-v', '--volume', type=float, default=1.0)
    p.add_argument('-t', '--tempo-scale', type=float, default=1.0)
    p.add_argument('-s', '--start', type=parse_time, default=0)
    p.add_argument('-p', '--progress', action='store_true', default=True, help='(default)')
    p.add_argument('-P', '--no-progress', dest='progress', action='store_false')
    p.add_argument('-E', '--print-events', action='store_true')
    p.add_argument('-S', '--sysex', action='store_true')
    p.add_argument('-L', '--loop', action='store_true')
    p.add_argument('-o', '--output', type=int)
    p.add_argument('-b', '--backend')
    p.add_argument('-T', '--length', action='store_true')
    p.add_argument('-i', '--info', action='store_true')
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
        events = MidiFile(args.file).schedule_events(meta=True)
        print(fmt_time(events[-1][1]))
    elif args.info:
        dump_info(MidiFile(args.file))
    else:
        play_midi(
            args.file, volume=args.volume, tempo_scale=args.tempo_scale,
            start=args.start, loop=args.loop, sysex=args.sysex,
            print_progress=args.progress, print_events=args.print_events,
            output=args.output)

if __name__ == '__main__':
    main()
