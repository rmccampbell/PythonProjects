#!/usr/bin/env python3
"""Extremely primitive MIDI synthesizer"""
import sys
import argparse
from dataclasses import dataclass, field, replace
from time import perf_counter

import numpy as np
import sounddevice as sd
import mido

import midi

@dataclass
class Note:
    frequency: float = 0.0
    velocity: int = 0
    ontime: float = 0.0
    offtime: float = np.inf

@dataclass
class Channel:
    notes: dict[int, Note] = field(default_factory=dict)
    program: int = 0
    pitch_bend: float = 0.0

class MidiSynth:
    def __init__(self, args):
        input_port = args.input_port
        if isinstance(input_port, int):
            input_port = mido.get_input_names()[input_port]
        self.input = mido.open_input(input_port, virtual=args.virtual_port)
        self.channels = [Channel() for i in range(16)]

        dev_info = sd.query_devices(args.output_device, 'output')
        self.sample_rate = dev_info['default_samplerate']
        self.start_idx = 0
        self.start_time = 0.0
        self.last_time = 0.0

        if args.envelope:
            self.envelope = getattr(self, 'envelope_' + args.envelope)
        if args.waveform:
            self.waveform = getattr(self, 'waveform_' + args.waveform)

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
        # print(f'{self.stream.time - time.currentTime:f} '
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

    def envelope_asr(self, t_on, t_off, t_att=.1, t_rel=.5):
        y = t_on/t_att
        np.minimum(y, 1-t_off/t_rel, out=y)
        np.clip(y, 0, 1, out=y)
        return y

    def envelope_adsr(self, t_on, t_off, t_att=.05, t_dec=.2, sus=.8, t_rel=.5):
        y = t_on/t_att
        dec_sus = np.maximum(1-(1-sus)/t_dec*(t_on-t_att), sus)
        np.minimum(y, dec_sus, out=y)
        np.minimum(y, sus*(1-t_off/t_rel), out=y)
        np.clip(y, 0, 1, out=y)
        return y

    def envelope_asr_exp(self, t_on, t_off, t_att=.05, t_rel=.5):
        y = 1. - np.exp(-4./t_att*t_on)
        y *= np.where(t_off < 0, 1, np.exp(-4./t_rel*t_off))
        # np.minimum(y, np.exp(-4./t_rel*t_off), out=y)
        np.clip(y, 0, 1, out=y)
        return y

    def envelope_adsr_exp(self, t_on, t_off, t_att=.05, t_dec=.2, sus=.8, t_rel=.5):
        y = 1. - np.exp(-4./t_att*t_on)
        y *= np.where(t_on < t_att, 1, np.exp(-4./t_dec*(t_on-t_att))*(1-sus)+sus)
        y *= np.where(t_off < 0, 1, np.exp(-4./t_rel*t_off))
        np.clip(y, 0, 1, out=y)
        return y

    envelope = envelope_adsr

    def waveform_sine(self, t):
        return np.sin(2*np.pi * t)

    def waveform_square(self, t):
        return 1 - 2*np.floor(2*t % 2)

    def waveform_saw(self, t):
        return (t - .5) % 1 * 2 - 1

    def waveform_tri(self, t):
        return abs((4*t - 1) % 4 - 2) - 1

    waveform = waveform_tri

    def process_msg(self, msg):
        channel = self.channels[msg.channel]
        if msg.type in ('note_on', 'note_off'):
            notes = channel.notes.copy()
            if msg.type == 'note_on' and msg.velocity:
                freq = midi.note_frequency(msg.note)
                notes[msg.note] = Note(freq, msg.velocity/127, self.stream.time)
            else:
                # notes.pop(msg.note, None)
                if note := notes.get(msg.note):
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
                             if self.stream.time - note.offtime < 1.}

    def run(self):
        with self.stream:
            while True:
                for msg in self.input.iter_pending():
                    self.process_msg(msg)
                self.flush_notes()


def main(args):
    try:
        with MidiSynth(args) as synth:
            print('Recieving midi messages... Press Ctr+C to quit')
            synth.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.exit(f'{type(e).__name__}: {e}')


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-l', '--list-ports', action='store_true',
        help='show list of midi input ports and exit')
    parser.add_argument(
        '-L', '--list-outputs', action='store_true',
        help='show list of audio output devices and exit')
    parser.add_argument(
        '-i', '--input-port', type=int_or_str,
        help='midi input port (numeric ID or string)')
    parser.add_argument(
        '-o', '--output-device', type=int_or_str,
        help='output device (numeric ID or string)')
    parser.add_argument(
        '-v', '--virtual-port', action='store_true',
        help='open a virtual midi input port')
    parser.add_argument(
        '-t', '--latency', type=float, default=.5,
        help='latency for audio output')
    parser.add_argument('-e', '--envelope')
    parser.add_argument('-w', '--waveform')
    args = parser.parse_args()
    if args.list_outputs:
        print(sd.query_devices())
        parser.exit()
    if args.list_ports:
        print('\n'.join(mido.get_input_names()))
        parser.exit()
    main(args)
