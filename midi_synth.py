#!/usr/bin/env python3
"""Extremely primitive MIDI synthesizer"""
import sys
import argparse
from dataclasses import dataclass, field, replace
import time
from typing import Dict

import numpy as np
import sounddevice as sd
import mido

def note_frequency(note):
    return 440.0 * 2**((note - 69) / 12)

@dataclass
class Note:
    frequency: float = 0.0
    velocity: int = 0
    ontime: float = 0.0
    offtime: float = np.inf

@dataclass
class Channel:
    notes: Dict[int, Note] = field(default_factory=dict)
    program: int = 0
    pitch_bend: float = 0.0

class MidiSynth:
    def __init__(self, args):
        input_port = args.input_port
        if isinstance(input_port, int) and not args.virtual_port:
            input_port = mido.get_input_names()[input_port]
        self.input = mido.open_input(input_port, virtual=args.virtual_port)
        self.channels = [Channel() for i in range(16)]

        dev_info = sd.query_devices(args.output_device, 'output')
        self.sample_rate = dev_info['default_samplerate']
        self.start_idx = 0
        self.start_time = 0.0
        self.last_time = 0.0

        self.waveform = getattr(self, 'waveform_' + args.waveform)
        self.envelope = getattr(self, 'envelope_' + args.envelope)
        self.attack = args.attack
        self.decay = args.decay
        self.sustain = args.sustain
        self.release = args.release

        self.stream = sd.OutputStream(
            device=args.output_device, samplerate=self.sample_rate, channels=1,
            latency=args.latency, callback=self.callback)

    def close(self):
        self.input.close()
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def callback(self, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if self.start_idx == 0:
            self.start_time = time.currentTime
        t = (self.start_idx + np.arange(frames)) / self.sample_rate + self.start_time
        t = t.reshape(-1, 1)
        self.synthesize(outdata, t)
        self.start_idx += frames
        # print(f'{time.currentTime:f} {self.stream.time - time.currentTime:f} '
        #       f'{time.outputBufferDacTime - time.currentTime:f} '
        #       f'{time.currentTime - self.last_time:f} {frames}')
        # self.last_time = time.currentTime

    def synthesize(self, output, t):
        output[:] = 0.0
        for channel in self.channels:
            for note in channel.notes.values():
                output += self.synthesize_note(t, note, channel)
        # output.clip(-1, 1, out=output)
        # np.tanh(output, out=output)
        output /= max(abs(output).max(), 1)

    def synthesize_note(self, t, note, channel):
        # print(note.ontime, note.offtime, t[0,0])
        # if note.ontime <= t[0,0] < note.offtime:
        amp = note.velocity
        freq = note.frequency * 2**(channel.pitch_bend / 6)
        envelope = self.envelope(t - note.ontime, t - note.offtime)
        return amp * envelope * self.waveform(freq * t)

    def envelope_flat(self, t_on, t_off):
        return np.float32((t_on >= 0) & (t_off < 0))

    def envelope_asr(self, t_on, t_off):
        y = t_on/self.attack
        np.minimum(y, 1-t_off/self.release, out=y)
        np.clip(y, 0, 1, out=y)
        return y

    def envelope_adsr(self, t_on, t_off):
        y = t_on/self.attack
        dec_sus = np.maximum(1-(1-self.sustain)/self.decay*(t_on-self.attack),
                             self.sustain)
        np.minimum(y, dec_sus, out=y)
        np.minimum(y, self.sustain*(1-t_off/self.release), out=y)
        np.clip(y, 0, 1, out=y)
        return y

    def envelope_asr_exp(self, t_on, t_off):
        y = 1. - np.exp(-4./self.attack*t_on)
        y *= np.where(t_off < 0, 1, np.exp(-4./self.release*t_off))
        # np.minimum(y, np.exp(-4./self.release*t_off), out=y)
        np.clip(y, 0, 1, out=y)
        return y

    def envelope_adsr_exp(self, t_on, t_off):
        y = 1. - np.exp(-4./self.attack*t_on)
        y *= np.where(
            t_on < self.attack, 1,
            np.exp(-4./self.decay*(t_on-self.attack))*(1-self.sustain)+self.sustain)
        y *= np.where(t_off < 0, 1, np.exp(-4./self.release*t_off))
        np.clip(y, 0, 1, out=y)
        return y

    def waveform_sine(self, t):
        return np.sin(2*np.pi * t)

    def waveform_square(self, t):
        return 1 - 2*np.floor(2*t % 2)

    def waveform_saw(self, t):
        return (t - .5) % 1 * 2 - 1

    def waveform_tri(self, t):
        return abs((4*t - 1) % 4 - 2) - 1

    def process_msg(self, msg):
        channel = self.channels[msg.channel]
        if msg.type in ('note_on', 'note_off'):
            notes = channel.notes.copy()
            if msg.type == 'note_on' and msg.velocity:
                freq = note_frequency(msg.note)
                notes[msg.note] = Note(freq, msg.velocity/127, self.stream.time)
            else:
                # notes.pop(msg.note, None)
                note = notes.get(msg.note)
                if note:
                    notes[msg.note] = replace(note, offtime=self.stream.time)
            channel.notes = notes
        elif msg.type == 'program_change':
            channel.program = msg.program
        elif msg.type == 'pitchwheel':
            channel.pitch_bend = msg.pitch / 8192

    def flush_notes(self):
        for ch in range(16):
            channel = self.channels[ch]
            channel.notes = {n: note for n, note in channel.notes.items()
                             if self.stream.time - note.offtime < self.release}

    def run(self):
        with self.stream:
            self.stream.start()
            while True:
                for msg in self.input.iter_pending():
                    self.process_msg(msg)
                self.flush_notes()
                time.sleep(.01)


def main(args):
    try:
        with MidiSynth(args) as synth:
            print('Recieving midi messages... Press Ctr+C to quit')
            synth.run()
    except KeyboardInterrupt:
        pass


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-l', '--list-ports', action='store_true',
                        help='show list of midi input ports and exit')
    parser.add_argument('-L', '--list-outputs', action='store_true',
                        help='show list of audio output devices and exit')
    parser.add_argument('-i', '--input-port', type=int_or_str,
                        help='midi input port (numeric ID or string)')
    parser.add_argument('-o', '--output-device', type=int_or_str,
                        help='output device (numeric ID or string)')
    parser.add_argument('-v', '--virtual-port', action='store_true',
                        help='open a virtual midi input port')
    parser.add_argument('-t', '--latency', type=float, default=.5,
                        help='latency for audio output')
    parser.add_argument('-w', '--waveform', default='tri',
                        choices=['sine', 'square', 'saw', 'tri'],
                        help='set the shape of the wave function')
    parser.add_argument('-e', '--envelope', default='adsr',
                        choices=['flat', 'asr', 'adsr', 'asr_exp', 'adsr_exp'],
                        help='set the envelope type')
    parser.add_argument('-a', '--attack', type=float, default=.05,
                        help='ADSR attack time')
    parser.add_argument('-d', '--decay', type=float, default=.2,
                        help='ADSR decay time')
    parser.add_argument('-s', '--sustain', type=float, default=.8,
                        help='ADSR sustain level')
    parser.add_argument('-r', '--release', type=float, default=.5,
                        help='ADSR release time')
    args = parser.parse_args()
    if args.list_outputs:
        # Some audio devices on windows have weird names with line breaks
        print(str(sd.query_devices()).replace('\r\n', ''))
        parser.exit()
    if args.list_ports:
        print('\n'.join(mido.get_input_names()))
        parser.exit()
    main(args)
