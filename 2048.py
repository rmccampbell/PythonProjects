#!/usr/bin/env python3
import sys, os, msvcrt, random

H = os.get_terminal_size()[1]

grid_fmt_u = '''\
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

grid_fmt_a = '''\
 _______________________________
|       |       |       |       |
| {:^5} | {:^5} | {:^5} | {:^5} |
|       |       |       |       |
|_______|_______|_______|_______|
|       |       |       |       |
| {:^5} | {:^5} | {:^5} | {:^5} |
|       |       |       |       |
|_______|_______|_______|_______|
|       |       |       |       |
| {:^5} | {:^5} | {:^5} | {:^5} |
|       |       |       |       |
|_______|_______|_______|_______|
|       |       |       |       |
| {:^5} | {:^5} | {:^5} | {:^5} |
|       |       |       |       |
|_______|_______|_______|_______|
'''

try:
    grid_fmt_u.encode(sys.stdout.encoding)
    grid_fmt = grid_fmt_u
except UnicodeEncodeError:
    grid_fmt = grid_fmt_a


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

def main():
    grid = [[0]*4 for i in range(4)]
    x, y = random.randrange(4), random.randrange(4)
    grid[y][x] = 2 if random.random() < .9 else 4
    while True:
        print('\n' * H)
        print(grid_fmt.format(*[i or '' for r in grid for i in r]))
        gridcp = [r[:] for r in grid]
        if not (move_up(gridcp) or move_down(gridcp) or
                move_left(gridcp) or move_right(gridcp)):
            print('Game over!')
            break
        moved = False
        k = msvcrt.getch()
        if msvcrt.kbhit():
            k += msvcrt.getch()
        if k == b'\xe0H':
            moved = move_up(grid)
        elif k == b'\xe0P':
            moved = move_down(grid)
        elif k == b'\xe0K':
            moved = move_left(grid)
        elif k == b'\xe0M':
            moved = move_right(grid)
        elif k in (b'\x1b', b'q'):
            break
        if moved:
            x, y = random.randrange(4), random.randrange(4)
            while grid[y][x]:
                x, y = random.randrange(4), random.randrange(4)
            grid[y][x] = 2 if random.random() < .9 else 4

if __name__ == '__main__':
    main()
