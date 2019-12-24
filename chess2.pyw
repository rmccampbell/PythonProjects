#!/usr/bin/env python3
"""Usage: chess2.pyw [WHITE_CPU=0] [BLACK_CPU=1] [MINIMAX_DEPTH=4]"""

import sys, os, random, threading
import pygame as pg

inf = float('inf')

DEBUG = False

### If you set BLACK_CPU to False, you can play in 2-player mode.
### Alternatively if you set WHITE_CPU to True you can watch it play itself ;)
WHITE_CPU = False
BLACK_CPU = True

### If you set MINIMAX_DEPTH to 5, it will get harder in theory. It will
### also get a lot slower.
### Warning: don't set it higher than 5 or it will take forever. 
MINIMAX_DEPTH = 4

# PyInstaller
if getattr(sys, 'frozen', False):
    DIR = sys._MEIPASS
else:
    DIR = os.path.dirname(sys.argv[0])
FONTFILE = os.path.join(DIR, 'data', 'old-english-text-mt.ttf')
IMAGEDIR = os.path.join(DIR, 'images/chess')

# Update delay in ms
TICK = 50

# Delay in ms before cpu finishes move
CPU_MOVE_DELAY = 600

# Dimensions
XMARGIN = 48
YMARGIN = 72
SQSIZE = 48
BRDSIZE = SQSIZE * 8
WIDTH = BRDSIZE + XMARGIN*2 # 480
HEIGHT = BRDSIZE + YMARGIN*2 # 528

# Colors
BGCOLOR = (128, 128, 128)
BCOLOR = (0, 0, 0)
WCOLOR = (255, 255, 255)
SELECT_COLOR = (0, 255, 255)
PROMOTE_COLOR = (255, 140, 0)
MOVE_COLOR = (0, 255, 255)
TXTCOLOR = (0, 0, 0)

# Sides
SIDES = ['WHITE', 'BLACK']
WHITE = 0
BLACK = 1

# Types
TYPES = ['PAWN', 'ROOK', 'KNIGHT', 'BISHOP', 'QUEEN', 'KING']
PAWN = 0
ROOK = 1
KNIGHT = 2
BISHOP = 3
QUEEN = 4
KING = 5

PIECE_VALUES_D = {PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9, KING: 100}
PIECE_VALUES = [PIECE_VALUES_D[i] for i in range(len(PIECE_VALUES_D))]


def load_image(name, convert=True):
    path = os.path.join(IMAGEDIR, name + '.png')
    img = pg.image.load(path)
    if convert:
        img = img.convert_alpha()
    return img

def grid2pix(x, y):
    return x*SQSIZE + XMARGIN, (7 - y)*SQSIZE + YMARGIN

def pix2grid(px, py):
    return (px - XMARGIN)//SQSIZE, 7 - (py - YMARGIN)//SQSIZE


class Game:
    piece_images = [[], []]
    title_image = None

    def __init__(self, white_cpu=WHITE_CPU, black_cpu=BLACK_CPU,
                 minimax_depth=MINIMAX_DEPTH):
        pg.init()
        pg.display.set_icon(load_image('chess_icon', False))
        pg.display.set_caption('Chess')
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.load_images()
        self.font1 = pg.font.Font(FONTFILE, 28)
        self.font2 = pg.font.Font(FONTFILE, 40)
        self.is_cpu = [white_cpu, black_cpu]
        self.minimax_depth = minimax_depth
        self.title()
        self.running = False
        # self.run()

    @classmethod
    def load_images(cls):
        names = [name.lower() for name in TYPES]
        cls.piece_images[WHITE] = [load_image(name + '_w') for name in names]
        cls.piece_images[BLACK] = [load_image(name + '_b') for name in names]
        cls.title_image = load_image('chess_title')
        cls.backdrop_image = load_image('backdrop')

    def run(self):
        self.running = True
        while self.running:
            self.events()
            self.update()
            if self.ingame:
                self.draw()
                pg.display.flip()
            pg.time.wait(TICK)

    def setup_board(self):
        self.board = board = [[None] * 8 for i in range(8)]
        order = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for x, typ in enumerate(order):
            board[x][0] = Piece(WHITE, typ)
            board[x][1] = Piece(WHITE, PAWN)
            board[x][6] = Piece(BLACK, PAWN)
            board[x][7] = Piece(BLACK, typ)
        self.king_pos = [(4, 0), (4, 7)]
        return board

    def title(self):
        self.ingame = False
        self.setup_board()
        self.draw_title()

    def gameover(self):
        if DEBUG: print('Game over!!1')
        self.ingame = False
        self.draw_gameover()

    def new_game(self):
        if DEBUG: print('\nNew game')
        self.ingame = True
        self.setup_board()
        self.start_turn(WHITE)

    def start_turn(self, turn):
        if DEBUG: print('\n%s turn' % SIDES[turn])
        self.turn = turn
        self.cpu_turn = self.is_cpu[turn]
        self.selected = None
        self.cpu_dest = None
        self.in_promotion = False
        self.check = self.is_check()
        if DEBUG and self.check: print('Check')
        if not self.any_moves_left() or self.is_draw():
            self.gameover()
            return
        if self.cpu_turn:
            self.start_cpu_turn()

    def update(self):
        if not self.ingame:
            return
        if self.cpu_turn:
            self.update_cpu()

    def events(self):
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                self.running = False
            elif evt.type == pg.KEYDOWN:
                if evt.key == pg.K_F4 and evt.mod & pg.KMOD_ALT or \
                   evt.key == pg.K_ESCAPE:
                    self.running = False
                elif evt.key in (pg.K_RETURN, pg.K_SPACE):
                    if not self.ingame:
                        self.new_game()
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if not self.ingame:
                    self.new_game()
                else:
                    self.click(*evt.pos)

    def click(self, px, py):
        if self.cpu_turn:
            return
        if self.in_promotion:
            self.pick_promotion(px, py)
            return
        x, y = pix2grid(px, py)
        if not (0 <= x < 8 and 0 <= y < 8):
            return
        piece = self.board[x][y]
        if (x, y) == self.selected:
            self.selected = None
        elif piece and piece.side == self.turn:
            self.selected = (x, y)
        elif self.selected:
            self.try_move(x, y)

    def pick_promotion(self, px, py):
        if 0 < HEIGHT - (YMARGIN - SQSIZE)//2 - py <= SQSIZE:
            i = (px - XMARGIN) // SQSIZE - 2
            if 0 <= i < 4:
                self.promote([QUEEN, KNIGHT, ROOK, BISHOP][i])

    def promote(self, typ):
        sx, sy = self.selected
        self.board[sx][sy] = Piece(self.turn, typ)
        self.next_turn()

    def try_move(self, x, y):
        if self.can_move(self.selected, (x, y)):
            self.move(self.selected, (x, y))

    def can_move(self, src, dest, test_check=True):
        (sx, sy), (dx, dy) = src, dest
        src_piece = self.board[sx][sy]
        dest_piece = self.board[dx][dy]
        if dest_piece and dest_piece.side == self.turn:
            return False
        if src_piece.can_move((sx, sy), (dx, dy), self.board):
            return not (test_check and self.move_is_check((sx, sy), (dx, dy)))
        return False

    def enum_moves(self, src, piece=None, test_check=True):
        piece = piece or self.board[src[0]][src[1]]
        return (move for move in piece.enum_moves(src, self.board)
                if not (test_check and self.move_is_check(src, move)))

    def move_is_check(self, src, dest):
        board = self.board
        (sx, sy), (dx, dy) = src, dest
        src_piece = board[sx][sy]
        dest_piece = board[dx][dy]
        board[sx][sy] = None
        board[dx][dy] = src_piece
        king_pos = None
        if src_piece.type == KING:
            king_pos = (dx, dy)
        check = self.is_check(king_pos)
        board[sx][sy] = src_piece
        board[dx][dy] = dest_piece
        return check

    def enum_pieces(self, side=None, board=None):
        board = board or self.board
        for x in range(8):
            for y in range(8):
                piece = board[x][y]
                if piece and side in (None, piece.side):
                    yield (x, y), piece

    def is_check(self, king_pos=None):
        board = self.board
        king_pos = king_pos or self.king_pos[self.turn]
        for pos, piece in self.enum_pieces(1 - self.turn):
            if piece.can_move(pos, king_pos, board):
                return True
        return False

    def move(self, src, dest):
        sx, sy = src
        dx, dy = dest
        piece = self.board[sx][sy]
        self.board[sx][sy] = None
        self.board[dx][dy] = piece
        if piece.type == PAWN and dy in (0, 7):
            self.start_promotion(dx, dy)
        else:
            if piece.type == KING:
                self.king_pos[piece.side] = (dx, dy)
            self.next_turn()

    def start_promotion(self, x, y):
        self.in_promotion = True
        self.selected = (x, y)
        if self.cpu_turn:
            self.cpu_promote()

    def next_turn(self):
        self.start_turn(1 - self.turn)

    def any_moves_left(self):
        for src, piece in self.enum_pieces(self.turn):
            for move in self.enum_moves(src, piece):
                return True
        return False

    # Only kings
    def is_draw(self):
        for src, piece in self.enum_pieces():
            if piece.type != KING:
                return False
        return True

    def draw_board(self):
        screen = self.screen
        for x in range(8):
            for y in range(8):
                color = (BCOLOR, WCOLOR)[(x + y) % 2]
                px, py = grid2pix(x, y)
                pg.draw.rect(screen, color, (px, py, SQSIZE, SQSIZE))
                piece = self.board[x][y]
                if piece:
                    screen.blit(piece.image, (px, py))

    def draw_title(self):
        screen = self.screen
        screen.fill(BGCOLOR)
        self.draw_board()

        rect = self.title_image.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(self.title_image, rect)
        pg.display.flip()

    def draw_gameover(self):
        self.draw()
        screen = self.screen
        if self.check:
            message1 = 'Checkmate'
            message2 = '%s Player Wins' % SIDES[1 - self.turn].title()
        else:
            message1 = 'Stalemate'
            message2 = 'Draw'
        rect = self.backdrop_image.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(self.backdrop_image, rect)
        txtimg = self.font2.render(message1, True, TXTCOLOR)
        rect = txtimg.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
        screen.blit(txtimg, rect)
        txtimg = self.font1.render(message2, True, TXTCOLOR)
        rect = txtimg.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
        screen.blit(txtimg, rect)
        pg.display.flip()

    def highlight(self, x, y, color=SELECT_COLOR):
        px, py = grid2pix(x, y)
        pg.draw.rect(self.screen, color, (px, py, SQSIZE, SQSIZE), 2)

    def draw(self):
        screen = self.screen
        screen.fill(BGCOLOR)

        self.draw_board()

        if self.selected:
            if self.in_promotion:
                self.highlight(*self.selected, PROMOTE_COLOR)
            else:
                if not self.cpu_turn:
                    for x, y in self.enum_moves(self.selected):
                        self.highlight(x, y, MOVE_COLOR)
                self.highlight(*self.selected, SELECT_COLOR)
        if self.cpu_dest:
            self.highlight(*self.cpu_dest, MOVE_COLOR)

        if self.in_promotion:
            self.draw_promotion()
        else:
            text = '%s Turn' % SIDES[self.turn].title()
            if self.cpu_turn:
                text += ' (Cpu)'
            txtimg = self.font1.render(text, True, TXTCOLOR)
            rect = txtimg.get_rect(center=(WIDTH//2, YMARGIN//2))
            screen.blit(txtimg, rect)
            if self.check:
                txtimg = self.font1.render('Check', True, TXTCOLOR)
                rect = txtimg.get_rect(center=(WIDTH//2, HEIGHT - YMARGIN//2))
                screen.blit(txtimg, rect)

    def draw_promotion(self):
        screen = self.screen
        for i in range(4):
            color = (WCOLOR, BCOLOR)[i % 2]
            px = XMARGIN + SQSIZE * (i + 2)
            py = HEIGHT - (YMARGIN + SQSIZE)//2
            pg.draw.rect(screen, color, (px, py, SQSIZE, SQSIZE))
            typ = [QUEEN, KNIGHT, ROOK, BISHOP][i]
            screen.blit(self.piece_images[self.turn][typ], (px, py))
        txtimg = self.font1.render('Choose Promotion', True, TXTCOLOR)
        rect = txtimg.get_rect(center=(WIDTH//2, YMARGIN//2))
        screen.blit(txtimg, rect)

    def start_cpu_turn(self):
        self.cpu_move_complete = False
        self.cpu_selection_timer = 0
        self.cpu_thread = threading.Thread(target=self.cpu_move_compute,
                                           daemon=True)
        self.cpu_thread.start()

    def update_cpu(self):
        if self.cpu_selection_timer:
            self.cpu_selection_timer -= 1
            if self.cpu_selection_timer == 0:
                src, dest = self.cpu_move_result
                assert self.can_move(src, dest)
                self.move(src, dest)
        elif self.cpu_move_complete:
            src, dest = self.cpu_move_result
            self.selected = src
            self.cpu_dest = dest
            self.cpu_selection_timer = CPU_MOVE_DELAY / TICK
            self.cpu_thread = None

    def cpu_move_compute(self):
        board = [row[:] for row in self.board]
        max_move, max_score = self.minimax(board, self.turn, self.minimax_depth)
        if DEBUG: print('max move: %s -> %s: %s' % (*max_move, max_score))
        self.cpu_move_result = max_move
        self.cpu_move_complete = True

    def minimax(self, board, turn, depth, alpha=-inf, beta=inf):
        if depth == 0:
            return None, self.score_board(board, turn)
        max_move = None
        max_score = -inf
        for src, piece in self.enum_pieces(turn, board):
            for dest in piece.enum_moves(src, board):
                if DEBUG and depth == self.minimax_depth:
                    print('minimax d=%s, %s -> %s: ' % (depth, src, dest), end='', flush=True)
                score = self.minimax_move(
                    board, turn, src, dest, depth, alpha, beta)
                if DEBUG and depth == self.minimax_depth:
                    print(score)
                if score > max_score:
                    max_score = score
                    max_move = (src, dest)
                    if max_score > alpha:
                        alpha = max_score
                        if alpha >= beta:
                            return max_move, max_score
        return max_move, max_score

    def minimax_move(self, board, turn, src, dest, depth, alpha, beta):
        (sx, sy), (dx, dy) = src, dest
        src_piece = board[sx][sy]
        dest_piece = board[dx][dy]
        if dest_piece and dest_piece.type == KING:
            # Multiply by depth to weight sooner checks higher
            return self.score_board(board, turn) + PIECE_VALUES[KING]*depth
        board[sx][sy] = None
        board[dx][dy] = src_piece
        if src_piece.type == PAWN and dy in (0, 7):
            board[dx][dy] = Piece(src_piece.side, QUEEN)
        move, score = self.minimax(board, 1 - turn, depth - 1, -beta, -alpha)
        board[sx][sy] = src_piece
        board[dx][dy] = dest_piece
        return -score

    def score_board(self, board, side):
        score = 0
        for x in range(8):
            for y in range(8):
                piece = board[x][y]
                if piece:
                    value = PIECE_VALUES[piece.type]
                    score += value if piece.side == side else -value
        return score + random.uniform(-1, 1)

    def cpu_promote(self):
        self.promote(QUEEN)


class Piece:
    def __init__(self, side, type):
        self.side = side
        self.type = type
        self.image = Game.piece_images[side][type]

    def __repr__(self):
        return 'Piece({}, {})'.format(SIDES[self.side], TYPES[self.type])

    def can_move(self, src, dest, board):
        if src == dest:
            return False
        typ = self.type
        x1, y1 = src
        x2, y2 = dest
        dx, dy = x2 - x1, y2 - y1
        sx = dx and dx // abs(dx)
        sy = dy and dy // abs(dy)

        if typ == PAWN:
            firstmove = y1 == (1, 6)[self.side] # (WHITE, BLACK)
            dir = (1, -1)[self.side]
            dest_piece = board[x2][y2]
            if firstmove and dx == 0 and dy == 2*dir:
                return not (dest_piece or board[x1][y1 + dir])
            elif dy == dir:
                return (dx == 0 and not dest_piece or
                        abs(dx) == 1 and dest_piece)

        elif typ == ROOK:
            if dx == 0:
                return not any(board[x1][y] for y in range(y1+sy, y2, sy))
            if dy == 0:
                return not any(board[x][y1] for x in range(x1+sx, x2, sx))

        elif typ == KNIGHT:
            return (abs(dx) == 2 and abs(dy) == 1 or
                    abs(dx) == 1 and abs(dy) == 2)

        elif typ == BISHOP:
            if abs(dx) == abs(dy):
                return not any(board[x][y] for (x, y) in
                    zip(range(x1+sx, x2, sx), range(y1+sy, y2, sy)))

        elif typ == QUEEN:
            if dx == 0:
                return not any(board[x1][y] for y in range(y1+sy, y2, sy))
            if dy == 0:
                return not any(board[x][y1] for x in range(x1+sx, x2, sx))
            if abs(dx) == abs(dy):
                return not any(board[x][y] for (x, y) in
                    zip(range(x1+sx, x2, sx), range(y1+sy, y2, sy)))

        elif typ == KING:
            return max(abs(dx), abs(dy)) == 1

        return False

    def enum_moves(self, src, board):
        otherside = 1 - self.side
        typ = self.type
        x1, y1 = src

        if typ == PAWN:
            dir = (1, -1)[self.side] # (WHITE, BLACK)
            if not board[x1][y1 + dir]:
                yield x1, y1 + dir
                firstmove = y1 == (1, 6)[self.side]
                if firstmove and not board[x1][y1 + 2*dir]:
                    yield x1, y1 + 2*dir
            if x1 > 0 and getside(board[x1 - 1][y1 + dir]) == otherside:
                yield x1 - 1, y1 + dir
            if x1 < 7 and getside(board[x1 + 1][y1 + dir]) == otherside:
                yield x1 + 1, y1 + dir

        elif typ == ROOK:
            for step, stop in ((1, 8), (-1, -1)):
                for x in range(x1 + step, stop, step):
                    piece = board[x][y1]
                    if not piece or piece.side == otherside:
                        yield x, y1
                    if piece:
                        break
                for y in range(y1 + step, stop, step):
                    piece = board[x1][y]
                    if not piece or piece.side == otherside:
                        yield x1, y
                    if piece:
                        break

        elif typ == KNIGHT:
            for dx, dy in [(-1, 2), (1, 2), (2, 1), (2, -1),
                           (1, -2), (-1, -2), (-2, -1), (-2, 1)]:
                x, y = x1 + dx, y1 + dy
                if (0 <= x < 8 and 0 <= y < 8 and
                        getside(board[x][y]) != self.side):
                    yield x, y

        elif typ == BISHOP:
            for xstep, xstop in ((1, 8), (-1, -1)):
                for ystep, ystop in ((1, 8), (-1, -1)):
                    for x, y in zip(range(x1 + xstep, xstop, xstep),
                                    range(y1 + ystep, ystop, ystep)):
                        piece = board[x][y]
                        if not piece or piece.side == otherside:
                            yield x, y
                        if piece:
                            break

        elif typ == QUEEN:
            for step, stop in ((1, 8), (-1, -1)):
                for x in range(x1 + step, stop, step):
                    piece = board[x][y1]
                    if not piece or piece.side == otherside:
                        yield x, y1
                    if piece:
                        break
                for y in range(y1 + step, stop, step):
                    piece = board[x1][y]
                    if not piece or piece.side == otherside:
                        yield x1, y
                    if piece:
                        break
            for xstep, xstop in ((1, 8), (-1, -1)):
                for ystep, ystop in ((1, 8), (-1, -1)):
                    for x, y in zip(range(x1 + xstep, xstop, xstep),
                                    range(y1 + ystep, ystop, ystep)):
                        piece = board[x][y]
                        if not piece or piece.side == otherside:
                            yield x, y
                        if piece:
                            break

        elif typ == KING:
            for dx, dy in [(0, 1), (1, 1), (1, 0), (1, -1),
                           (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
                x, y = x1 + dx, y1 + dy
                if (0 <= x < 8 and 0 <= y < 8 and
                        getside(board[x][y]) != self.side):
                    yield x, y


def getside(piece):
    return piece and piece.side


def main():
    global game
    white_cpu, black_cpu = WHITE_CPU, BLACK_CPU
    minimax_depth = MINIMAX_DEPTH
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        # Won't print if run via pythonw.exe
        print(__doc__)
        return
    if len(sys.argv) > 2:
        white_cpu = bool(int(sys.argv[1]))
        black_cpu = bool(int(sys.argv[2]))
    if len(sys.argv) > 3:
        minimax_depth = int(sys.argv[3])
    try:
        game = Game(white_cpu, black_cpu, minimax_depth)
        game.run()
    finally:
        pg.quit()


if __name__ == '__main__':
    main()
