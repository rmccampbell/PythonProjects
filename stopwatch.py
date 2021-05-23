#!/usr/bin/env python3
import sys, time, argparse

stemp = '{}:{:02}'
cstemp = '{}:{:02}:{:02}'

def stopwatch(hundredths=False):
    dt = .01 if hundredths else 1
    temp = cstemp if hundredths else stemp
    starttime = time.time()
    print()
    print(temp.format(0, 0, 0), end='', flush=True)
    try:
        while True:
            time.sleep(dt)
            eltime = time.time() - starttime
            m = int(eltime // 60)
            s = int(eltime % 60)
            ms = int((eltime % 1)*100)
            print('\r' + temp.format(m, s, ms) + ' \b',
                  end='', flush=True)
    except KeyboardInterrupt:
        print()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-H', '--hundredths', action='store_true')
    args = p.parse_args()
    stopwatch(args.hundredths)
