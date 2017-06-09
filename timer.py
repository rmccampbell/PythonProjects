#!/usr/bin/env python3
import sys, time, argparse

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
    import win32ui, win32con
    def show_msgbox():
        win32ui.MessageBox("Time's Up!", "Timer", win32con.MB_SYSTEMMODAL |
                           win32con.MB_ICONWARNING)
except ImportError:
    def show_msgbox():
        pass

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('minutes', type=int)
    p.add_argument('seconds', nargs='?', default=0, type=int)
    p.add_argument('-s', '--showsecs', action='store_true')
    p.add_argument('-n', '--nomsgbox', action='store_false', dest='msgbox')
    args = p.parse_args()
    timer(args.minutes, args.seconds, showsecs=args.showsecs,
          msgbox=args.msgbox)
