#!/usr/bin/env python3
"""Shows a progress bar on the windows taskbar"""
import comtypes.client as cc
import win32console
import enum

TBPF_NOPROGRESS = 0
TBPF_INDETERMINATE = 0x1
TBPF_NORMAL = 0x2
TBPF_ERROR = 0x4
TBPF_PAUSED = 0x8

tbl = cc.GetModule('data\\TaskbarLib.tlb')
taskbar = cc.CreateObject('{56FDF344-FD6D-11d0-958A-006097C9A090}', interface=tbl.ITaskbarList3)
taskbar.HrInit()

hwnd = win32console.GetConsoleWindow()

if __name__ == '__main__':
    import tqdm, time
    try:
        taskbar.SetProgressState(hwnd, TBPF_NORMAL)
        for t in tqdm.trange(50):
            taskbar.SetProgressValue(hwnd, t, 50)
            time.sleep(0.1)
    finally:
        taskbar.SetProgressState(hwnd, TBPF_NOPROGRESS)
