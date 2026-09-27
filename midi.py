#!/usr/bin/env python3
import os, struct, enum, time, re, math, warnings, builtins
from collections.abc import ByteString, Callable, Collection, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, BinaryIO, Final, Generic, NamedTuple, NewType, TypeGuard, TypeVar, cast
import numpy as np

# Standard MIDI file spec: https://midi.org/standard-midi-files

########################
# MIDI Enums/Constants #
########################

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
    KeyPress   = 0xa0
    CtrlChange = 0xb0
    ProgChange = 0xc0
    ChannPress = 0xd0
    PitchBend  = 0xe0

    SysEx      = 0xf0
    SysExEsc   = 0xf7
    Meta       = 0xff

    NonMidi    = 0xf0

NoteOff: Final = MidiStatus.NoteOff
NoteOn: Final = MidiStatus.NoteOn
KeyPress: Final = MidiStatus.KeyPress
CtrlChange: Final = MidiStatus.CtrlChange
ProgChange: Final = MidiStatus.ProgChange
ChannPress: Final = MidiStatus.ChannPress
PitchBend: Final = MidiStatus.PitchBend
SysEx: Final = MidiStatus.SysEx
SysExEsc: Final = MidiStatus.SysExEsc
Meta: Final = MidiStatus.Meta
NonMidi: Final = MidiStatus.NonMidi

MIDI_EVENTS = {s for s in MidiStatus if s < NonMidi}

class MetaEvent(HexInt, enum.Enum):
    SeqNumber   = 0x00
    TextEvent   = 0x01
    Copyright   = 0x02
    TrackName   = 0x03
    InstrName   = 0x04
    Lyric       = 0x05
    Marker      = 0x06
    CuePoint    = 0x07
    ProgramName = 0x08
    DeviceName  = 0x09
    ChannPrefix = 0x20
    MIDIPort    = 0x21
    EndOfTrack  = 0x2f
    SetTempo    = 0x51
    SMPTEOff    = 0x54
    TimeSig     = 0x58
    KeySig      = 0x59
    SecSpecific = 0x7f

META_INT_EVENTS = {
    MetaEvent.SeqNumber,
    MetaEvent.ChannPrefix,
    MetaEvent.MIDIPort,
    MetaEvent.SetTempo
}

META_TEXT_EVENTS = {
    MetaEvent.TextEvent,
    MetaEvent.Copyright,
    MetaEvent.TrackName,
    MetaEvent.InstrName,
    MetaEvent.Lyric,
    MetaEvent.Marker,
    MetaEvent.CuePoint,
    MetaEvent.ProgramName,
    MetaEvent.DeviceName,
}


DEFAULT_TEMPO = 500_000


######################
# MIDI Message Types #
######################

@dataclass
class _StatusMeta:
    fields: tuple[str, ...]
    field_handler: Callable[..., dict[str, int]]

def _pitchbend_args(pitch_lo, pitch_hi=None):
    if pitch_hi is None:
        pitch_lo, pitch_hi = pitch_bend_bytes(pitch_lo)
    return {'pitch_lo': pitch_lo, 'pitch_hi': pitch_hi}

_STATUS_TO_META = {
    NoteOff: _StatusMeta(
        ('note', 'velocity'),
        lambda note, velocity: {'note': note, 'velocity': velocity}),
    NoteOn: _StatusMeta(
        ('note', 'velocity'),
        lambda note, velocity: {'note': note, 'velocity': velocity}),
    KeyPress: _StatusMeta(
        ('note', 'value'), lambda note, value: {'note': note, 'value': value}),
    CtrlChange: _StatusMeta(
        ('control', 'value'),
        lambda control, value: {'control': control, 'value': value}),
    ProgChange: _StatusMeta(
        ('program',), lambda program: {'program': program}),
    ChannPress: _StatusMeta(('value',), lambda value: {'value': value}),
    PitchBend: _StatusMeta(('pitch_lo', 'pitch_hi'), _pitchbend_args),
}


class Message:
    pass


class MidiMessage(Message):
    bytes: builtins.bytes
    type: MidiStatus
    channel: int
    data: tuple[int, ...]

    # Type-specific fields
    note: int  # NoteOn, NoteOff, KeyPress
    velocity: int  # NoteOn, NoteOff
    value: int  # KeyPress, CtrlChange
    control: int  # CtrlChange
    program: int  # ProgChange
    pitch: int  # PitchBend
    pitch_lo: int  # PitchBend
    pitch_hi: int  # PitchBend

    @classmethod
    def from_buffer(cls, status: int, buff: ByteString, off=0) -> tuple['MidiMessage', int]:
        buff = bytes(buff)
        typ = MidiStatus(status & STATUS_MASK)
        channel = status & CHANNEL_MASK
        end = off + len(_STATUS_TO_META[typ].fields)
        return cls(typ, channel, *buff[off: end]), end

    def __init__(self, type_or_bytes: MidiStatus | int | ByteString,
                 channel: int | None = None, *args, **kwargs):
        if channel is not None:
            self.type = MidiStatus(type_or_bytes)
            self.channel = channel
            fields = _STATUS_TO_META[self.type].field_handler(*args, **kwargs)
            self.data = tuple(fields.values())
            self.bytes = bytes([self.type | self.channel, *self.data])
        else:
            if isinstance(type_or_bytes, int):
                raise TypeError('single argument must be bytes-like')
            self.bytes = bts = bytes(type_or_bytes)
            self.type = MidiStatus(bts[0] & STATUS_MASK)
            self.channel = bts[0] & CHANNEL_MASK
            self.data = tuple(bts[1:])
            fields = _STATUS_TO_META[self.type].field_handler(*self.data)
        vars(self).update(fields)
        if self.type == PitchBend:
            self.pitch = pitch_bend_value(*self.data)

    def __eq__(self, other):
        return isinstance(other, MidiMessage) and self.bytes == other.bytes

    def __hash__(self):
        return hash(self.bytes)

    def __bytes__(self):
        return self.bytes

    def __repr__(self):
        if self.type == PitchBend:
            data = f'pitch={self.pitch}'
        else:
            fields = _STATUS_TO_META[self.type].fields
            data = ', '.join(f'{k}={v!r}' for k, v in zip(fields, self.data))
        tname = type(self).__name__
        return f'{tname}({self.type}, channel={self.channel}, {data})'


class SysExMessage(Message):
    data: bytes
    __slots__ = ('data',)

    @classmethod
    def from_buffer(cls, status: int, buff: ByteString, off=0) -> tuple['SysExMessage', int]:
        assert status in (SysEx, SysExEsc)
        length, off = parse_vlq(buff, off)
        end = off + length
        prefix = b'\xf0' if status == SysEx else b''
        data = prefix + bytes(buff[off: end])
        return cls(data), end

    def __init__(self, data: ByteString):
        self.data = bytes(data)

    def __eq__(self, other):
        return isinstance(other, SysExMessage) and self.data == other.data

    def __hash__(self):
        return hash(self.data)

    def __bytes__(self):
        return self.data

    def __repr__(self):
        return f'{type(self).__name__}({self.data!r})'


class MetaMessage(Message):
    type: int
    data: bytes

    # Type-specific fields
    # Int-typed events
    value: int
    # Text-typed events
    text: str
    # SMPTEOff
    hour: int
    minute: int
    second: int
    frame: int
    frac_frame: int
    # TimeSig
    num: int
    denom: int
    cc: int
    bb: int
    # KeySig
    key: int
    is_minor: bool

    @classmethod
    def from_buffer(cls, buff: ByteString, off=0) -> tuple['MetaMessage', int]:
        typ = buff[off]
        length, off = parse_vlq(buff, off + 1)
        end = off + length
        data = bytes(buff[off: end])
        return cls(typ, data), end

    def __init__(self, typ: int, data: ByteString):
        try:
            self.type = MetaEvent(typ)
        except ValueError:
            self.type = typ
        self.data = bytes(data)
        vars(self).update(self._parse_data(self.type, self.data))

    def __eq__(self, other):
        return (isinstance(other, MetaMessage)
                and self.type == other.type and self.data == other.data)

    def __hash__(self):
        return hash((self.type, self.data))

    def __repr__(self):
        if len(vars(self)) > 2:
            fields = ', '.join(f'{k}={v!r}' for k, v in vars(self).items()
                               if k not in ('type', 'data'))
            return f'<{type(self).__name__} type={self.type}, {fields}>'
        elif self.data:
            return f'<{type(self).__name__} type={self.type}, data={self.data!r}>'
        return f'<{type(self).__name__} type={self.type}>'

    @staticmethod
    def _parse_data(typ, data) -> dict[str, Any]:
        if typ in META_INT_EVENTS:
            return {'value': int.from_bytes(data, 'big')}
        elif typ in META_TEXT_EVENTS:
            return {'text': try_decode(data.rstrip(b'\0'))}
        elif typ == MetaEvent.SMPTEOff:
            return dict(zip(
                ('hour', 'minute', 'second', 'frame', 'frac_frame'), data))
        elif typ == MetaEvent.TimeSig:
            return {'num': data[0], 'denom': 2**data[1],
                    'cc': data[2], 'bb': data[3]}
        elif typ == MetaEvent.KeySig:
            return dict(zip(('key', 'is_minor'), struct.unpack('b?', data)))
        return {}


RelTicks = NewType('RelTicks', float)
AbsTicks = NewType('AbsTicks', float)
AbsTime = NewType('AbsTime', float)
type AnyAbs = AbsTicks | AbsTime

T = TypeVar('T', bound=float, covariant=True)
M = TypeVar('M', bound=Message, covariant=True, default=Message)

class Event(NamedTuple, Generic[T, M]):
    message: M
    time: T

type RelEvent[M: Message = Message] = Event[RelTicks, M]
type AbsEvent[M: Message = Message] = Event[AbsTicks, M]
type AbsTimeEvent[M: Message = Message] = Event[AbsTime, M]
type AnyAbsEvent[M: Message = Message] = Event[AnyAbs, M]

def rel_to_abs[M: Message](events: list[RelEvent[M]]) -> list[AbsEvent[M]]:
    abs_events = []
    tick = 0
    for evt in events:
        tick += evt.time
        abs_events.append(Event(evt.message, AbsTicks(tick)))
    return abs_events


def abs_to_rel[M: Message](events: list[AbsEvent[M]]) -> list[RelEvent[M]]:
    rel_events = []
    lasttick = 0
    for evt in events:
        rel_events.append(Event(evt.message, RelTicks(evt.time - lasttick)))
        lasttick = evt.time
    return rel_events


##########################
# MIDI File Class/Parser #
##########################

@dataclass
class SmpteDivision:
    fps: int
    tpf: int

class MidiFile:
    tracks: list[list[RelEvent]]
    division: int | SmpteDivision
    format: int

    def __init__(self, file_or_tracks: str | BinaryIO | list[list[RelEvent]],
                 division: int | SmpteDivision = 480, format=1):
        if isinstance(file_or_tracks, list):
            self.tracks = [list(track) for track in file_or_tracks]
            self.division = division
            self.format = format
        else:
            self._read(file_or_tracks)

    def __repr__(self):
        return (f'<MidiFile ntracks={len(self.tracks)} '
                f'division={self.division} format={self.format}>')

    def merged_events(self) -> list[AbsEvent]:
        events: list[AbsEvent] = []
        for track in self.tracks:
            events.extend(rel_to_abs(track))
        events.sort(key=lambda evt: evt.time)
        return events

    def tick_duration(self, tempo: int) -> float:
        if isinstance(self.division, SmpteDivision):
            return 1 / (self.division.fps * self.division.tpf)
        else:
            return tempo / (self.division * 1000_000)

    def schedule_events(self, sysex=False, meta=False) -> list[AbsTimeEvent]:
        tempo = DEFAULT_TEMPO
        sec_per_tick = self.tick_duration(tempo)
        events: list[AbsTimeEvent] = []
        last_tick = last_ts = 0
        for msg, tick in self.merged_events():
            ts = last_ts + (tick - last_tick) * sec_per_tick
            last_tick, last_ts = tick, ts
            if isinstance(msg, MetaMessage) and msg.type == MetaEvent.SetTempo:
                tempo = msg.value
                sec_per_tick = self.tick_duration(tempo)
            if (isinstance(msg, MidiMessage)
                    or sysex and isinstance(msg, SysExMessage)
                    or meta and isinstance(msg, MetaMessage)):
                events.append(Event(msg, AbsTime(ts)))
        return events

    def _read(self, file: BinaryIO | str):
        if isinstance(file, str):
            with open(file, 'rb') as file:
                buffer = file.read()
        else:
            buffer = file.read()
        fname = getattr(file, 'name', '<buffer>')

        chunk_head_fmt = struct.Struct('>4sI')
        header_data_fmt = struct.Struct('>HHh')
        fail_msg = f'failed to parse midi file {fname}'
        warn_msg = f'while parsing midi file {fname}'

        def read_chunk(buffer: bytes, offset=0) -> tuple[bytes, bytes, int]:
            typ, length = chunk_head_fmt.unpack_from(buffer, offset)
            offset += chunk_head_fmt.size
            data = buffer[offset: offset + length]
            return typ, data, offset + length

        try:
            # Header chunk
            typ, data, i = read_chunk(buffer)
            if typ != b'MThd':
                raise ValueError(f'{fail_msg}: no header chunk found')
            fmt, ntracks, div = header_data_fmt.unpack_from(data)
            if div & 0x8000:
                div = SmpteDivision(-(div >> 8), div & 0xff)
            self.format, self.division = fmt, div
            self.tracks = []

            # Track chunks
            while i < len(buffer) and len(self.tracks) < ntracks:
                typ, data, i = read_chunk(buffer, i)
                if typ == b'MTrk':
                    self.tracks.append(parse_track_data(data))
                elif typ == b'MThd':
                    raise ValueError(f'{fail_msg}: multiple header chunks found')
                else:
                    warnings.warn(f'{warn_msg}: unknown chunk type: {typ}')
        except (struct.error, IndexError) as e:
            raise ValueError(f'{fail_msg}: unexpected end of file') from e

        if i < len(buffer):
            warnings.warn(f'{warn_msg}: extra {len(buffer) - i} bytes found at end of file')
        if len(self.tracks) != ntracks:
            warnings.warn(f'{warn_msg}: found {len(self.tracks)} tracks, expected {ntracks}')

type _MidiFileParam = str | BinaryIO | MidiFile

def _as_midi_file(file: _MidiFileParam) -> MidiFile:
    if isinstance(file, MidiFile):
        return file
    return MidiFile(file)


def parse_track_data(buffer: bytes, offset=0, length=-1) -> list[RelEvent]:
    i = offset
    end = offset + length if length >= 0 else len(buffer)
    events: list[RelEvent] = []
    running_status = None
    while i < end:
        dt, i = parse_vlq(buffer, i)
        status = buffer[i]
        i += 1
        # Sysex Event
        if status in (SysEx, SysExEsc):
            running_status = None
            msg, i = SysExMessage.from_buffer(status, buffer, i)
        # Meta Event
        elif status == Meta:
            running_status = None
            msg, i = MetaMessage.from_buffer(buffer, i)
        # MIDI Event
        else:
            # Running status
            if not status & 0x80:
                if running_status is None:
                    raise ValueError('invalid running status')
                status = running_status
                i -= 1
            running_status = status
            msg, i = MidiMessage.from_buffer(status, buffer, i)
        events.append(Event(msg, RelTicks(dt)))
    return events


def parse_vlq(data: ByteString, offset=0) -> tuple[int, int]:
    i = offset
    n = 0
    msb = 1
    while msb:
        b = data[i]
        n = n << 7 | b & 0x7f
        msb = b >> 7
        i += 1
    return n, i


########################
# MIDI Event Utilities #
########################

def is_note_on(msg: Message) -> TypeGuard[MidiMessage]:
    return (isinstance(msg, MidiMessage)
            and msg.type == NoteOn and msg.velocity > 0)

def is_note_off(msg: Message) -> TypeGuard[MidiMessage]:
    return (isinstance(msg, MidiMessage)
            and (msg.type == NoteOff
                 or (msg.type == NoteOn and msg.velocity == 0)))


def end_time[E: AnyAbsEvent](events: list[E]) -> float:
    return events[-1].time if events else 0


def shift_events[E: AnyAbsEvent](events: list[E], dt) -> list[E]:
    return [Event(msg, ts+dt) for msg, ts in events]


def slice_events[E: AnyAbsEvent](events: list[E], start, end=None) -> list[E]:
    if end is None:
        end = end_time(events)
    return [Event(msg, ts-start) for msg, ts in events if start <= ts <= end]


type _OneOrSet[T] = T | Collection[T]


def filter_events[T: float, M: Message, M2: Message = M](
        events: Iterable[Event[T, M]],
        cls: type[M2] | tuple[type[M2], ...] | None = None,
        types: _OneOrSet[MidiStatus | MetaEvent | int] | None = None,
        channel: _OneOrSet[int] | None = None, *,
        exclude: _OneOrSet[type[Message] | MidiStatus | MetaEvent | int] = (),
        note_on=False, note_off=False) -> list[Event[T, M2]]:
    if types is not None and not isinstance(types, Collection):
        types = (types,)
    elif types is None and (note_on or note_off):
        types = ()
    if channel is not None and not isinstance(channel, Collection):
        channel = (channel,)
    if not isinstance(exclude, Collection):
        exclude = (exclude,)
    exclude_classes = tuple([t for t in exclude if isinstance(t, type)])
    typed_classes = (MidiMessage, MetaMessage)

    events = list(events)
    ret: list[Event[T, M2]] = []
    for msg, ts in events:
        if cls is not None and not isinstance(msg, cls):
            continue
        if types is not None and not (
                (isinstance(msg, typed_classes) and msg.type in types)
                or (note_on and is_note_on(msg))
                or (note_off and is_note_off(msg))):
            continue
        if (exclude and (
                isinstance(msg, exclude_classes)
                or (isinstance(msg, typed_classes) and msg.type in exclude))):
            continue
        if (channel is not None and not (
                isinstance(msg, MidiMessage) and msg.channel in channel)):
            continue
        ret.append(Event(cast(M2, msg), ts))
    return ret


def get_notes(file: _MidiFileParam | None = None,
              events: list[AbsEvent] | list[AbsTimeEvent] | None = None,
              off=False, ticks=False):
    if events is None:
        assert file is not None
        file = _as_midi_file(file)
        events = file.merged_events() if ticks else file.schedule_events()
    noteon = np.array(
        [(t, m.note) for m, t in events if is_note_on(m)]).reshape(-1, 2)
    if not off:
        return noteon[:, 0], noteon[:, 1]
    noteoff = np.array(
        [(t, m.note) for m, t in events if is_note_off(m)]).reshape(-1, 2)
    indon = np.argsort(noteon[:, 1], kind='mergesort')
    indoff = np.argsort(noteoff[:, 1], kind='mergesort')
    noteoff[indon] = noteoff[indoff]
    return noteon[:, 0], noteoff[:, 0], noteon[:, 1]


def get_notes_mido(midofile, off=False, ticks=False):
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
# MIDI Player Utilities #
#########################

NOTE_MAP = {
    'Cb': -1,  'C':  0,  'C#':  1,  'Db':  1,  'D':  2,  'D#':  3,
    'Eb':  3,  'E':  4,  'E#':  5,  'Fb':  4,  'F':  5,  'F#':  6,
    'Gb':  6,  'G':  7,  'G#':  8,  'Ab':  8,  'A':  9,  'A#': 10,
    'Bb': 10,  'B': 11,  'B#': 12,
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

type _Note = int | str

def parse_note(note: _Note) -> int:
    if isinstance(note, int):
        return note
    match = re.fullmatch(r'([A-Ga-g][#b♯♭]?)(-?[0-9])?', note)
    if not match:
        raise ValueError(f'invalid note: {note}')
    name, num = match.groups()
    name = name[0].upper() + name[1:].replace('♯', '#').replace('♭', 'b')
    num = int(num) if num else 4
    return NOTE_MAP[name] + 12*(num + 1)

def note_name(note: int) -> str:
    return NOTE_NAMES[note % 12] + str(note // 12 - 1)

def note_frequency(note: _Note) -> float:
    if isinstance(note, str):
        note = parse_note(note)
    return 440.0 * 2**((note - 69) / 12)

def frequency_to_note(freq: float | np.ndarray) -> int | np.ndarray:
    if isinstance(freq, np.ndarray):
        return (np.round(np.log2(freq / 440.0) * 12) + 69).astype(int)
    return round(math.log2(freq / 440.0) * 12) + 69


def tempo_to_bpm(tempo: float) -> float:
    return 1000_000 * 60 / tempo

def tempo_from_bpm(bpm: float) -> float:
    return 1000_000 * 60 / bpm


def scale(start: _Note, end: _Note | None, intervals: list[int]) -> list[int]:
    start = parse_note(start)
    end = parse_note(end) if end is not None else start + 12
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

def chromatic_scale(start: _Note, end: _Note | None = None):
    return scale(start, end, [1])

def major_scale(start: _Note, end: _Note | None = None):
    return scale(start, end, MAJOR_SCALE)

def natural_minor_scale(start: _Note, end: _Note | None = None):
    return scale(start, end, NATURAL_MINOR_SCALE)

def harmonic_minor_scale(start: _Note, end: _Note | None = None):
    return scale(start, end, HARMONIC_MINOR_SCALE)


def chord(root: _Note, intervals: list[int], inversion: int = 0) -> list[int]:
    root = parse_note(root)
    nnotes = len(intervals)
    return [root + interval + ((inversion + nnotes - i - 1) // nnotes * 12)
            for i, interval in enumerate(intervals)]

MAJOR = [0, 4, 7]
MINOR = [0, 3, 7]
DIMINISHED = [0, 3, 6]
AUGMENTED = [0, 4, 8]
DOM_7TH = [0, 4, 7, 10]
MAJOR_7TH = [0, 4, 7, 11]
MINOR_7TH = [0, 3, 7, 10]
MIN_MAJ_7TH = [0, 3, 7, 11]


def pitch_bend_bytes(p: int | float) -> tuple[int, int]:
    if isinstance(p, float):
        p = round(p * 8192)
    x = min(max(p + 8192, 0), 16383)
    return x & 127, x >> 7

def pitch_bend_value(lowb: int, highb: int) -> int:
    x = highb << 7 | lowb
    return x - 8192

def pitch_bend_float(lowb: int, highb: int) -> float:
    return pitch_bend_value(lowb, highb) / 8192


INSTRUMENT_NAMES = [
    # Piano
    'Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano',
    'Honky-tonk Piano', 'Electric Piano 1', 'Electric Piano 2', 'Harpsichord',
    'Clavinet',
    # Chromatic Percussion
    'Celesta', 'Glockenspiel', 'Music Box', 'Vibraphone', 'Marimba',
    'Xylophone', 'Tubular Bells', 'Dulcimer',
    # Organ
    'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ',
    'Reed Organ', 'Accordion', 'Harmonica', 'Tango Accordion',
    # Guitar
    'Acoustic Guitar (nylon)', 'Acoustic Guitar (steel)',
    'Electric Guitar (jazz)', 'Electric Guitar (clean)',
    'Electric Guitar (muted)', 'Overdriven Guitar', 'Distortion Guitar',
    'Guitar harmonics',
    # Bass
    'Acoustic Bass', 'Electric Bass (finger)', 'Electric Bass (pick)',
    'Fretless Bass', 'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1',
    'Synth Bass 2',
    # Strings
    'Violin', 'Viola', 'Cello', 'Contrabass', 'Tremolo Strings',
    'Pizzicato Strings', 'Orchestral Harp', 'Timpani',
    # Ensemble
    'String Ensemble 1', 'String Ensemble 2', 'Synth Strings 1',
    'Synth Strings 2', 'Choir Aahs', 'Voice Oohs', 'Synth Voice',
    'Orchestra Hit',
    # Brass
    'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet', 'French Horn',
    'Brass Section', 'Synth Brass 1', 'Synth Brass 2',
    # Reed
    'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax', 'Oboe',
    'English Horn', 'Bassoon', 'Clarinet',
    # Pipe
    'Piccolo', 'Flute', 'Recorder', 'Pan Flute', 'Blown Bottle', 'Shakuhachi',
    'Whistle', 'Ocarina',
    # Synth Lead
    'Lead 1 (square)', 'Lead 2 (sawtooth)', 'Lead 3 (calliope)',
    'Lead 4 (chiff)', 'Lead 5 (charang)', 'Lead 6 (voice)', 'Lead 7 (fifths)',
    'Lead 8 (bass + lead)',
    # Synth Pad
    'Pad 1 (new age)', 'Pad 2 (warm)', 'Pad 3 (polysynth)', 'Pad 4 (choir)',
    'Pad 5 (bowed)', 'Pad 6 (metallic)', 'Pad 7 (halo)', 'Pad 8 (sweep)',
    # Synth Effects
    'FX 1 (rain)', 'FX 2 (soundtrack)', 'FX 3 (crystal)', 'FX 4 (atmosphere)',
    'FX 5 (brightness)', 'FX 6 (goblins)', 'FX 7 (echoes)', 'FX 8 (sci-fi)',
    # Ethnic
    'Sitar', 'Banjo', 'Shamisen', 'Koto', 'Kalimba', 'Bag pipe', 'Fiddle',
    'Shanai',
    # Percussive
    'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock', 'Taiko Drum',
    'Melodic Tom', 'Synth Drum', 'Reverse Cymbal',
    # Sound Effects
    'Guitar Fret Noise', 'Breath Noise', 'Seashore', 'Bird Tweet',
    'Telephone Ring', 'Helicopter', 'Applause', 'Gunshot',
]

INSTRUMENTS = {k.lower(): i for i, k in enumerate(INSTRUMENT_NAMES)}

PERCUSSION_CHANNEL = 9

NON_PERC_CHANNELS = set(range(16)) - {PERCUSSION_CHANNEL}

type _Instr = int | str

###############
# MIDI Player #
###############

class MidiPlayer:
    def __new__(cls, output=None, instrument=None):
        if cls is MidiPlayer:
            cls = get_player_class()
        return super(MidiPlayer, cls).__new__(cls)

    def __init__(self, output=None, instrument: _Instr | None = None):
        try:
            if instrument is not None:
                self.set_instrument(instrument)
        except:
            self.close()
            raise

    @staticmethod
    def list_outputs() -> list[str]:
        raise NotImplementedError

    def send_message(
            self, message: MidiMessage | SysExMessage | Sequence[int]):
        raise NotImplementedError

    def send_sysex(self, message: SysExMessage | Sequence[int]):
        self.send_message(message)

    def note_on(self, note: _Note, velocity=127, channel=0):
        self.send_message([NoteOn + channel, parse_note(note), velocity])

    def note_off(self, note: _Note, velocity=0, channel=0):
        self.send_message([NoteOff + channel, parse_note(note), velocity])

    def pitch_bend(self, bend: int | float, channel=0):
        self.send_message([PitchBend + channel, *pitch_bend_bytes(bend)])

    def all_notes_off(self, channel: int | None = None, fallback=True):
        channels = [channel] if channel is not None else range(16)
        for ch in channels:
            # Channel Mode 120: All Sound Off
            self.send_message([CtrlChange + ch, 120, 0])
            if fallback:
                for note in range(128):
                    self.note_off(note, channel=ch)

    def set_instrument(self, instrument: _Instr, channel=0):
        if isinstance(instrument, str):
            instrument = INSTRUMENTS[instrument.lower()]
        self.send_message([ProgChange + channel, instrument])

    def wait(self, duration=1.0):
        if duration > 0:
            time.sleep(duration)

    def time(self):
        return time.perf_counter()

    def play_midi(self, file: _MidiFileParam | None = None,
                  events: list[AbsTimeEvent] | None = None, volume=1,
                  tempo_scale=1, start=0, loop=False, sysex=False,
                  print_progress=True, print_events=False):
        if events is None:
            assert file is not None
            events = _as_midi_file(file).schedule_events(sysex=True, meta=True)
        if print_events:
            print_progress = False
        tottime = end_time(events) / tempo_scale
        notes_on = set()
        last_ts = 0
        try:
            do_loop = True
            while do_loop:
                last_ts = 0
                t0 = self.time() - start
                for msg, ts in events:
                    ts /= tempo_scale
                    if (ts < start and isinstance(msg, MidiMessage)
                        and msg.type in (NoteOn, NoteOff)):
                        continue
                    # Print before waiting to hide delay
                    if print_progress and last_ts != ts and last_ts >= start:
                        print(f'\r{fmt_time(last_ts)}/{fmt_time(tottime)}',
                              end='', flush=True)
                    elif print_events:
                        print(msg)
                    self.wait(ts + t0 - self.time())
                    if sysex and isinstance(msg, SysExMessage):
                        self.send_sysex(msg)
                    elif isinstance(msg, MidiMessage):
                        if is_note_on(msg):
                            if volume != 1:
                                velocity = min(int(msg.velocity*volume), 127)
                                msg = MidiMessage(msg.type, msg.channel,
                                                  msg.note, velocity)
                            notes_on.add((msg.channel, msg.note))
                        elif is_note_off(msg):
                            notes_on.discard((msg.channel, msg.note))
                        self.send_message(msg)
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

    def play_note(self, note: _Note | None, duration=1.0, velocity=127,
                  channel=0, instrument: _Instr | None = None):
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
                   time_scale=1.0, channel=0, instrument: _Instr | None = None):
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

    def play_chord(self, notes, duration=1.0, velocity=127, channel=0,
                   instrument: _Instr | None = None):
        if instrument is not None:
            self.set_instrument(instrument, channel)
        try:
            for note in notes:
                self.note_on(note, velocity, channel)
            self.wait(duration)
        finally:
            for note in notes:
                self.note_off(note, channel=channel)

    def close(self):
        pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


#################
# MIDI Backends #
#################

_backend: str | None = None

DEFAULT_BACKEND = 'rtmidi'

def set_backend(backend: str | None):
    global _backend
    if backend and backend not in _PLAYER_CLASSES:
        raise ValueError(f'unknown backend: {backend}')
    _backend = backend

def get_backend() -> str:
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
            raise ValueError(f'unknown backend: {_backend}')
    return _backend

def get_player_class() -> type[MidiPlayer]:
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
    def list_outputs() -> list[str]:
        import rtmidi
        output = rtmidi.MidiOut()
        return output.get_ports()

    def send_message(self, message):
        self.output.send_message(bytes(message))

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
    def list_outputs() -> list[str]:
        import pygame.midi
        pygame.midi.init()
        infos = []
        for i in range(pygame.midi.get_count()):
            devinfo = pygame.midi.get_device_info(i)
            if devinfo[3]:
                infos.append(try_decode(devinfo[1]))
        return infos

    def send_message(self, message):
        bts = bytes(message)
        if len(bts) > 3:
            self.send_sysex(bts)
        else:
            self.output.write_short(*bts)

    def send_sysex(self, message):
        self.output.write_sys_ex(0, bytes(message))

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


def play_midi(file: _MidiFileParam | None = None,
              events: list[AbsTimeEvent] | None = None, volume=1, tempo_scale=1,
              start=0, loop=False, sysex=False, print_progress=True,
              print_events=False, output=None):
    with MidiPlayer(output) as player:
        player.play_midi(
            file=file, events=events, volume=volume, tempo_scale=tempo_scale,
            start=start, loop=loop, sysex=sysex, print_progress=print_progress,
            print_events=print_events)


def play_notes(notes, duration=0.5, delay=0.0, velocity=127, time_scale=1,
               channel=0, instrument: _Instr | None = None, output=None):
    with MidiPlayer(output) as player:
        player.play_notes(notes, duration, delay, velocity, time_scale,
                          channel, instrument)
        player.wait(.5)


def all_notes_off(output=None):
    with MidiPlayer(output) as player:
        player.all_notes_off(fallback=True)


def list_outputs() -> list[str]:
    return get_player_class().list_outputs()


def try_decode(bts: bytes) -> str:
    try:
        return bts.decode('utf-8')
    except UnicodeDecodeError:
        return bts.decode('cp1252', 'replace')


def dump_info(mf: MidiFile):
    events = mf.schedule_events(meta=True)
    time_fmt = fmt_time(end_time(events))
    tempo_evts = filter_events(events, MetaMessage, MetaEvent.SetTempo)
    tempos = {m.value for m, _ in tempo_evts} or [DEFAULT_TEMPO]
    tempos_bpm = sorted(map(tempo_to_bpm, tempos))
    tempo_fmt = '/'.join(str(round(t)) for t in tempos_bpm[:3])
    tempo_fmt += '…' * (len(tempos_bpm) > 3)
    nnotes = len(filter_events(events, note_on=True))
    format_fmt = f'format: {mf.format}, ' if mf.format != 1 else ''
    print(f'# Tracks: {len(mf.tracks)}, {format_fmt}duration: {time_fmt}, '
          f'division: {mf.division}, tempo: {tempo_fmt} bpm, notes: {nnotes}, '
          f'events: {len(events)}')

    info_types = {MetaEvent.TextEvent: 'Text',
                  MetaEvent.Copyright: 'Copyright'}
    first_track = (mf.tracks or [[]])[0]
    for msg, dt in filter_events(first_track, MetaMessage, info_types):
        print(f'{info_types[MetaEvent(msg.type)]}: {msg.text.rstrip()}')

    for i, track in enumerate(mf.tracks):
        name_evts = filter_events(track, MetaMessage, MetaEvent.TrackName)
        name = name_evts[0].message.text if name_evts else ''
        prog_evts = filter_events(
            track, MidiMessage, ProgChange, NON_PERC_CHANNELS)
        instrs = [*{INSTRUMENT_NAMES[m.program]: None for m, _ in prog_evts}]
        note_evts = filter_events(track, MidiMessage, note_on=True)
        channels = {m.channel for m, _ in note_evts}
        if PERCUSSION_CHANNEL in channels:
            instrs.append('Percussion')
        instr_lbl = ', '.join(instrs)
        nnotes = len(note_evts)

        name_fmt = name and f' ({name})'
        instr_fmt = instr_lbl and f'{instr_lbl}, '
        print(f'Track {i+1}{name_fmt}: {instr_fmt}{nnotes} notes, '
              f'{len(track)} events')


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('file', nargs='?')
    p.add_argument('-v', '--volume', type=float, default=1.0)
    p.add_argument('-t', '--tempo-scale', type=float, default=1.0)
    p.add_argument('-s', '--start', type=parse_time, default=0)
    p.add_argument('-p', '--progress', action='store_true', default=True,
                   help='(default)')
    p.add_argument('-P', '--no-progress', dest='progress',
                   action='store_false')
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
        print(fmt_time(end_time(events)))
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
