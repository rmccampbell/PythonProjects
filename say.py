#!/usr/bin/env python3
import sys, os, re
import warnings
import argparse
import pyttsx3

def say(text, voice=None):
    engine = pyttsx3.init()
    if voice:
        pattern = r'(^|\W|\b)%s(\W|\b|$)' % re.escape(voice)
        for v in engine.getProperty('voices'):
            if re.search(pattern, v.name, re.IGNORECASE):
                engine.setProperty('voice', v.id)
                break
        else:
            warnings.warn('voice "%s" not found' % voice)
    engine.say(text)
    engine.runAndWait()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('args', nargs='*')
    p.add_argument('-v', '--voice')
    p.add_argument('-l', '--list-voices', action='store_true')
    args = p.parse_args()
    if args.list_voices:
        engine = pyttsx3.init()
        for v in engine.getProperty('voices'):
            print(v.name)
        return
    if args.args:
        for arg in args.args:
            if os.path.exists(arg):
                say(open(arg, encoding='utf-8').read(), args.voice)
            else:
                say(arg, args.voice)
    else:
        say(sys.stdin.read(), args.voice)

if __name__ == '__main__':
    main()
