#!/usr/bin/python3
import sys, pygame, math, random

G = 10000
T = .1

DELAY = 1

PARTICLES = [
    (1620, 3980,   3,  -2, 15),
    (3460, 2610, -10,   6,  5),
    (1180, 3620,  -7,  -5,  8),
    (2570, 2210,   9,   4, 10),
    (2300, 1180,  -3,   2,  9),
    (1360, 1620,  -8,  -9, 14),
    (1520, 1730,   6,  -4,  8),
    (3200, 2180,  -2,  -1, 12),
    (2510, 3920,  -5,   3,  8),
    (1470, 1670,  -1,  -9,  1),
    (3980, 3240,  -5,  -7, 25),
    (3450, 1340,   3,   2, 12),
    (3030, 1930,   8,   9,  2),
    (3310, 2120,   6,  -8, 12),
    (3410, 1210,  -5,  -2, 14),
    (1520, 2320,   1, -10,  4),
    (2570, 2450,  10,   0,  9),
    (3270, 1830,   3,   4,  5),
    (3710, 1460,   8,  -8,  1),
    (3940, 1190,   8,  -2,  4),
    (3560, 1220,  10,  -7, 10),
    (2060, 2210, -10,  -8, 13),
    (1090, 2710,   9,  -9, 14),
    (2330, 2310,  -6,   6,  7),
    (1590, 1300,   0,   2, 10),
    (3740, 2800,   5,   0, 13),
    (3240, 1530,   9,   3, 12),
]

def main(file=None, bounce=False, wrap=False):
    if file:
        particles = read(file)
    else:
##        particles = PARTICLES
        particles = []
        for i in range(15):
            x = random.uniform(500, 4500)
            y = random.uniform(500, 4500)
            vx = random.uniform(-4, 4)
            vy = random.uniform(-4, 4)
            m = abs(random.gauss(8, 2))
            particles.append((x, y, vx, vy, m))
    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    running = True
    while running:
        screen.fill((255, 255, 255))

        xsum, ysum, mtot = 0, 0, 0
        for x, y, vx, vy, m in particles:
            xsum += x * m
            ysum += y * m
            mtot += m

        cmx, cmy = xsum / mtot, ysum / mtot

        for i, (x, y, vx, vy, m) in enumerate(particles):
            px = int(x // 10)
            py = int(y // 10)
            pr = int(math.sqrt(m)) + 1
            pygame.draw.circle(screen, (0, 0, 255), (px, py), pr)

            mrest = mtot - m
            xrest = (xsum - x*m) / mrest
            yrest = (ysum - y*m) / mrest
            dx, dy = xrest - x, yrest - y
            r = math.sqrt(dx**2 + dy**2)
            ax = G*mrest*dx/r**3 if r > 1e-3 else 0
            ay = G*mrest*dy/r**3 if r > 1e-3 else 0

##            v = math.sqrt(vx**2 + vy**2)
##            pvx = 5*vx/math.sqrt(v) if v else 0
##            pvy = 5*vy/math.sqrt(v) if v else 0
##            pxv = int(x//10 + pvx)
##            pyv = int(y//10 + pvy)
##            pygame.draw.line(screen, (0, 255, 0), (px, py), (pxv, pyv))
##            pxa = int(x//10 + 50*ax)
##            pya = int(y//10 + 50*ay)
##            pygame.draw.line(screen, (255, 0, 0), (px, py), (pxa, pya))

            x += vx * T
            y += vy * T
            vx += ax * T
            vy += ay * T

            if bounce:
                if not 0 <= x < 5000:
                    vx *= -1
                if not 0 <= y < 5000:
                    vy *= -1
            if wrap:
                x %= 5000
                y %= 5000

            particles[i] = (x, y, vx, vy, m)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if (e.key == pygame.K_ESCAPE or
                    e.key == pygame.K_F4 and e.mod & pygame.KMOD_ALT):
                    running = False

        pygame.time.wait(DELAY)

def read(file):
    if file == '-':
        file = sys.stdin
    elif isinstance(file, str):
        file = open(file)
    p = []
    for l in file:
        x, y, vx, vy, m = map(float, l.split())
        p.append((x, y, vx, vy, m))
    return p

if __name__ == '__main__':
    try:
        main(*sys.argv[1:])
    finally:
        pygame.quit()
