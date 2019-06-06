#!/usr/bin/env python3
import sys, argparse, ctypes
import os.path as op
from winreg import *

##SendMessage = ctypes.windll.user32.SendMessageW
SendMessageTimeout = ctypes.windll.user32.SendMessageTimeoutW
HWND_BROADCAST = 0xffff
WM_SETTINGCHANGE = 0x1a
SMTO_NORMAL = 0

def main(add=None, index=None, remove=None, contains=(), system=False,
         lines=False):
    if system:
        key = HKEY_LOCAL_MACHINE
        subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    else:
        key, subkey = HKEY_CURRENT_USER, 'Environment'
    if add is not None or remove is not None:
        mode = KEY_ALL_ACCESS
    else:
        mode = KEY_READ
    with OpenKey(key, subkey, 0, mode) as key:
        value, typ = QueryValueEx(key, 'Path')
        values = value.split(';')
        if contains:
            values = {op.normcase(op.normpath(op.expandvars(val)))
                      for val in values}
            for path in contains:
                if op.normcase(op.abspath(path)) in values:
                    print('"%s" in path' % path)
                else:
                    print('"%s" not in path' % path)
            return
        if remove is not None:
            if remove not in values:
                print('"%s" not in path' % remove)
                return
            values.remove(remove)
        if add is not None:
            if add in values:
                print('"%s" already in path' % add)
                return
            if index is None:
                index = len(values)
            values.insert(index, add)
        if add is not None or remove is not None:
            value = ';'.join(values)
            typ = REG_EXPAND_SZ if value.count('%') >= 2 else REG_SZ
            SetValueEx(key, 'Path', 0, typ, value)
##            SendMessage(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment')
            SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                               'Environment', SMTO_NORMAL, 100, 0)
            print('** Registry updated **')
    if lines:
        value = value.replace(';', '\n')
    print(value)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add')
    parser.add_argument('-i', '--index', type=int)
    parser.add_argument('-r', '--remove')
    parser.add_argument('-c', '--contains', default=[], action='append')
    parser.add_argument('-s', '--system', action='store_true')
    parser.add_argument('-l', '--lines', action='store_true')
    args = parser.parse_args()
    main(**vars(args))
