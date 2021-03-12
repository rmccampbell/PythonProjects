#!/usr/bin/env python3
import curses, random, argparse
from curses import ascii

QUIT_KEYS = {ascii.ESC, ord('q'), ascii.ctrl(ord('C'))}

GRID_FMT = '''\
┌───────┬───────┬───────┬───────┐
│       │       │       │       │
│ {:^5} │ {:^5} │ {:^5} │ {:^5} │
│       │       │       │       │
├───────┼───────┼───────┼───────┤
│       │       │       │       │
│ {:^5} │ {:^5} │ {:^5} │ {:^5} │
│       │       │       │       │
├───────┼───────┼───────┼───────┤
│       │       │       │       │
│ {:^5} │ {:^5} │ {:^5} │ {:^5} │
│       │       │       │       │
├───────┼───────┼───────┼───────┤
│       │       │       │       │
│ {:^5} │ {:^5} │ {:^5} │ {:^5} │
│       │       │       │       │
└───────┴───────┴───────┴───────┘
'''


def copy_grid(grid):
    return [r[:] for r in grid]

def make_positive(grid):
    for y in range(4):
        for x in range(4):
            grid[y][x] = abs(grid[y][x])

def move_up(grid):
    moved = False
    for i in range(3, 0, -1):
        for y in range(i):
            for x in range(4):
                if grid[y][x] == 0 and grid[y+1][x]:
                    grid[y][x] = grid[y+1][x]
                    grid[y+1][x] = 0
                    moved = True
                elif grid[y][x] > 0 and grid[y][x] == grid[y+1][x]:
                    grid[y][x] *= -2
                    grid[y+1][x] = 0
                    moved = True
    make_positive(grid)
    return moved

def move_down(grid):
    moved = False
    for i in range(3):
        for y in range(3, i, -1):
            for x in range(4):
                if grid[y][x] == 0 and grid[y-1][x]:
                    grid[y][x] = grid[y-1][x]
                    grid[y-1][x] = 0
                    moved = True
                elif grid[y][x] > 0 and grid[y][x] == grid[y-1][x]:
                    grid[y][x] *= -2
                    grid[y-1][x] = 0
                    moved = True
    make_positive(grid)
    return moved

def move_left(grid):
    moved = False
    for i in range(3, 0, -1):
        for x in range(i):
            for y in range(4):
                if grid[y][x] == 0 and grid[y][x+1]:
                    grid[y][x] = grid[y][x+1]
                    grid[y][x+1] = 0
                    moved = True
                elif grid[y][x] > 0 and grid[y][x] == grid[y][x+1]:
                    grid[y][x] *= -2
                    grid[y][x+1] = 0
                    moved = True
    make_positive(grid)
    return moved

def move_right(grid):
    moved = False
    for i in range(3):
        for x in range(3, i, -1):
            for y in range(4):
                if grid[y][x] == 0 and grid[y][x-1]:
                    grid[y][x] = grid[y][x-1]
                    grid[y][x-1] = 0
                    moved = True
                elif grid[y][x] > 0 and grid[y][x] == grid[y][x-1]:
                    grid[y][x] *= -2
                    grid[y][x-1] = 0
                    moved = True
    make_positive(grid)
    return moved

def spawn(grid):
    x, y = random.randrange(4), random.randrange(4)
    while grid[y][x]:
        x, y = random.randrange(4), random.randrange(4)
    grid[y][x] = 2 if random.random() < .9 else 4

# def draw(scr, grid):
#     for y in range(0, 17, 4):
#         for x in range(1, 32):
#             if x % 8 != 0:
#                 scr.addch(y, x, curses.ACS_HLINE)
#         if 4 <= y <= 12:
#             scr.addch(y, 0, curses.ACS_LTEE)
#             scr.addch(y, 32, curses.ACS_RTEE)
#             for x in range(8, 25, 8):
#                 scr.addch(y, x, curses.ACS_PLUS)
#     for x in range(0, 33, 8):
#         for y in range(1, 16):
#             if y % 4 != 0:
#                 scr.addch(y, x, curses.ACS_VLINE)
#         if 8 <= x <= 24:
#             scr.addch(0, x, curses.ACS_TTEE)
#             scr.addch(16, x, curses.ACS_BTEE)
#     scr.addch(0, 0, curses.ACS_ULCORNER)
#     scr.addch(0, 32, curses.ACS_URCORNER)
#     scr.addch(16, 0, curses.ACS_LLCORNER)
#     scr.addch(16, 32, curses.ACS_LRCORNER)
#     for i in range(4):
#         for j in range(4):
#             val = grid[i][j]
#             if val:
#                 scr.addstr(i*4 + 2, j*8 + 2, format(val, '^5'))
#     scr.refresh()

def draw(scr, grid):
    txt = GRID_FMT.format(*[i or '' for r in grid for i in r])
    for i, line in enumerate(txt.splitlines()):
        scr.addstr(i, 0, line)
    scr.refresh()

def push_state(grid):
    grid_hist.append((grid, random.getstate()))

def pop_state():
    if not grid_hist:
        return None
    grid, state = grid_hist.pop()
    random.setstate(state)
    return grid

def main(scr, init_board=None):
    global grid_hist
    curses.curs_set(0)
    h, w = scr.getmaxyx()
    win = scr.subwin((h-1)//2 - 8, (w-1)//2 - 16)

    grid_hist = []

    grid = init_board or [[0]*4 for i in range(4)]
    for i in range(2):
        spawn(grid)

    while True:
        win.clear()
        draw(win, grid)
        gridcp = copy_grid(grid)
        if not (move_up(gridcp) or move_down(gridcp) or
                move_left(gridcp) or move_right(gridcp)):
            win.addstr(18, 0, 'Game over!')
            win.refresh()
            while scr.getch() not in {*QUIT_KEYS, ord('\n')}:
                pass
            break
        oldgrid = copy_grid(grid)
        moved = False
        k = scr.getch()
        if k == curses.KEY_UP:
            moved = move_up(grid)
        elif k == curses.KEY_DOWN:
            moved = move_down(grid)
        elif k == curses.KEY_LEFT:
            moved = move_left(grid)
        elif k == curses.KEY_RIGHT:
            moved = move_right(grid)
        elif k in (ascii.BS, curses.KEY_BACKSPACE):
            grid = pop_state() or grid
        elif k in QUIT_KEYS:
            break
        if moved:
            push_state(oldgrid)
            spawn(grid)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-b', '--init-board')
    args = p.parse_args()
    init_board = None
    if args.init_board:
        init_board = [list(map(int, row)) for row in args.init_board.split('|')]
    curses.wrapper(main, init_board)
