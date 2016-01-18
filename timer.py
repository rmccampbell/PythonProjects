#!/usr/bin/env python3
import sys, time

def timer(minutes, seconds=0, showsecs=False, msgbox=True):
    seconds += minutes * 60
    curtime = time.time()
    rtime = seconds
    endtime = curtime + rtime
    print()
    print("{}:{:02}".format(rtime // 60, rtime % 60), end='', flush=True)

    try:
        while curtime < endtime:
            time.sleep(1)
            curtime = time.time()
            rtime = round(endtime - curtime)
            if showsecs or rtime < 60 or rtime % 60 == 0:
                print("\r{}:{:02} \b".format(rtime // 60, rtime % 60),
                      end='', flush=True)

        print()
        print("Time's Up!\a")
        if msgbox:
            show_msgbox()

    except KeyboardInterrupt:
        print("\r{}:{:02} ".format(rtime // 60, rtime % 60))

try:
    import win32ui
    def show_msgbox():
        win32ui.MessageBox("Time's Up!", "Timer")
except ImportError:
    def show_msgbox():
        pass

if __name__ == '__main__':
    timer(*map(int, sys.argv[1:]))
