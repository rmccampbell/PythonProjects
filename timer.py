#!/usr/bin/env python3
import sys, time, argparse

def timer(minutes, seconds=0, showsecs=True, msgbox=True):
    seconds += minutes * 60
    curtime = time.time()
    rtime = seconds
    endtime = curtime + rtime
    print()
    print("{}:{:02}".format(rtime // 60, rtime % 60), end='', flush=True)

    try:
        while rtime > 0:
            time.sleep(1)
            curtime = time.time()
            rtime = round(endtime - curtime)
            if showsecs or rtime < 60 or rtime % 60 == 0:
                print("\r{}:{:02} \b".format(rtime // 60, rtime % 60),
                      end='', flush=True)

        print()
        print("Time's Up!")
        if msgbox and show_msgbox:
            show_msgbox()
        else:
            print('\a', end='')

    except KeyboardInterrupt:
        print("\r{}:{:02} ".format(rtime // 60, rtime % 60))

try:
    import win32ui, win32con
    def show_msgbox():
        win32ui.MessageBox("Time's Up!", "Timer", win32con.MB_SYSTEMMODAL |
                           win32con.MB_ICONWARNING)
except ImportError:
    show_msgbox = None

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('minutes')
    p.add_argument('seconds', nargs='?', default=0, type=int)
    p.add_argument('-S', '--noshowsecs', dest='showsecs', action='store_false')
    p.add_argument('-M', '--nomsgbox', dest='msgbox', action='store_false')
    args = p.parse_args()
    if ':' in args.minutes:
        try:
            args.minutes, args.seconds = map(int, args.minutes.split(':'))
        except ValueError as e:
            p.error(e)
    else:
        try:
            args.minutes = int(args.minutes)
        except ValueError as e:
            p.error(e)
    timer(args.minutes, args.seconds, showsecs=args.showsecs,
          msgbox=args.msgbox)
