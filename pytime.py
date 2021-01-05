#!/usr/bin/env python3
import sys, time, shutil, subprocess, argparse

def format_time(time):
    if time >= 60:
        min, sec = divmod(time, 60)
        hour, min = divmod(min, 60)
        return f'{hour:.0f}:{min:02.0f}:{sec:05.2f}'
    else:
        return f'{time:.4f}s'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i', '--input', action='store_true')
    p.add_argument('-l', '--lines', action='store_true')
    p.add_argument('-S', '--noshell', dest='shell', action='store_false')
    p.add_argument('-c', '--command')
    p.add_argument('command_args', metavar='COMMAND [ARGS...]',
                   nargs=argparse.REMAINDER)
    args = p.parse_args()
    if args.input:
        start = time.perf_counter()
        shutil.copyfileobj(sys.stdin, sys.stdout)
        end = time.perf_counter()
        print('Time:', format_time(end - start))
    elif args.lines:
        while True:
            start = time.perf_counter()
            line = sys.stdin.readline()
            end = time.perf_counter()
            sys.stdout.write(line)
            print('Time:', format_time(end - start))
    else:
        command = args.command or args.command_args
        start = time.perf_counter()
        try:
            subprocess.call(command, shell=args.shell)
        except Exception as e:
            sys.exit('{}: {}'.format(type(e).__name__, e))
        end = time.perf_counter()
        print('Time:', format_time(end - start))

if __name__ == '__main__':
    main()
