#!/usr/bin/env python3
import os, time, msvcrt

W, H = 45, 23
TH = os.get_terminal_size()[1]

CONT = 0
WIN = 1
LOSE = 2
QUIT = -1

def update():
    global bx, by, vx, vy, p1, p2, score, paused
    if msvcrt.kbhit():
        k = msvcrt.getch()
        if msvcrt.kbhit():
            k += msvcrt.getch()
        if k == b'\xe0K' and not paused:
            p1 -= 2
        elif k == b'\xe0M' and not paused:
            p1 += 2
        elif k == b'p':
            paused = not paused
        elif k in (b'\x1b', b'q'):
            return QUIT
    if paused:
        return CONT
    p1 = max(4, min(W-5, p1))
    p2 = max(4, min(W-5, bx))
    bx += vx
    by += vy
    if bx == 0 or bx == W-1:
        vx = -vx
    if by == 1 and abs(bx - p2) < 5:
        vy = -vy
    if by == H-2 and abs(bx - p1) < 5:
        vy = -vy
        score += 1
    if by < 0:
        return WIN
    if by >= H:
        return LOSE
    return CONT

def draw():
    print('\n'*(TH-H), end='')
    a = [[' ']*W for i in range(H)]
    a[by][bx] = 'O'
    a[H-1][p1-4:p1+5] = ['=']*9
    a[0][p2-4:p2+5] = ['=']*9
    for r in a:
        print('|' + ''.join(r) + '|')
    print('score:', score, end='', flush=True)

def main():
    global bx, by, vx, vy, p1, p2, score, paused
    bx = 12
    by = 10
    vx = 1
    vy = 1
    p1 = 22
    p2 = bx
    score = 0
    paused = False

    print('\n'*1000, end='')
    st = CONT
    while st == CONT:
        draw()
        time.sleep(.1)
        st = update()

    os.system('cls')
    if st == LOSE:
        print('\nYou lose!')
    elif st == WIN:
        print('\nYou win!')
    if st != QUIT:
        print('\nYour score was:', score)

if __name__ == '__main__':
    main()
