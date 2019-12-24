#!/usr/bin/env python3
import sys, os
import pygame as pg

DIR = os.path.dirname(sys.argv[0])
FONTFILE = os.path.join(DIR, 'data', 'old-english-text-mt.ttf')

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
WHITE = 0
BLACK = 1

# Types
PAWN = 0
ROOK = 1
KNIGHT = 2
BISHOP = 3
QUEEN = 4
KING = 5


def load_image(name, convert=True):
    path = os.path.join(DIR, 'images/chess', name + '.png')
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

    def __init__(self):
        pg.init()
        pg.display.set_icon(load_image('chess_icon', False))
        pg.display.set_caption('Chess')
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.load_images()
        self.font1 = pg.font.Font(FONTFILE, 28)
        self.font2 = pg.font.Font(FONTFILE, 40)
        self.title()
        self.running = False
        # self.run()

    @classmethod
    def load_images(cls):
        names = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
        cls.piece_images[WHITE] = [load_image(name + '_w') for name in names]
        cls.piece_images[BLACK] = [load_image(name + '_b') for name in names]
        cls.title_image = load_image('chess_title')
        cls.backdrop_image = load_image('backdrop')

    def run(self):
        self.running = True
        while self.running:
            if self.ingame:
                self.draw()
                pg.display.flip()
            self.events()
            pg.time.wait(50)

    def title(self):
        self.ingame = False
        screen = self.screen
        screen.fill(BGCOLOR)

        self.setup_board()
        self.draw_board()

        rect = self.title_image.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(self.title_image, rect)
        pg.display.flip()

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

    def new_game(self):
        self.ingame = True
        self.setup_board()
        self.start_turn(WHITE)

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
            self.move(x, y)

    def can_move(self, src, dest):
        (sx, sy), (dx, dy) = src, dest
        src_piece = self.board[sx][sy]
        dest_piece = self.board[dx][dy]
        if dest_piece and dest_piece.side == self.turn:
            return False
        if src_piece.can_move((sx, sy), (dx, dy), self.board):
            return not self.move_is_check((sx, sy), (dx, dy))
        return False

    def enum_moves(self, x, y):
        return (move for move in
                self.board[x][y].enum_moves((x, y), self.board)
                if not self.move_is_check((x, y), move))

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

    def is_check(self, king_pos=None):
        board = self.board
        king_pos = king_pos or self.king_pos[self.turn]
##        for x in range(8):
##            for y in range(8):
##                piece = board[x][y]
##                if piece and piece.type == KING and piece.side == self.turn:
##                    king_pos = (x, y)
##                    break
        for x in range(8):
            for y in range(8):
                piece = board[x][y]
                if piece and piece.side != self.turn and \
                   piece.can_move((x, y), king_pos, board):
                    return True
        return False

    def move(self, x, y):
        sx, sy = self.selected
        piece = self.board[sx][sy]
        self.board[sx][sy] = None
        self.board[x][y] = piece
        if piece.type == PAWN and y in (0, 7):
            self.start_promotion(x, y)
        else:
            if piece.type == KING:
                self.king_pos[piece.side] = (x, y)
            self.next_turn()

    def start_promotion(self, x, y):
        self.in_promotion = True
        self.selected = (x, y)

    def next_turn(self):
        self.start_turn(1 - self.turn)

    def start_turn(self, turn):
        self.turn = turn
        self.selected = None
        self.in_promotion = False
        self.check = self.is_check()
        if not self.any_moves_left():
            self.gameover()

    def any_moves_left(self):
        board = self.board
        for sx in range(8):
            for sy in range(8):
                piece = board[sx][sy]
                if piece and piece.side == self.turn:
                    for move in self.enum_moves(sx, sy):
                        return True
##                    for dx in range(8):
##                        for dy in range(8):
##                            if self.can_move((sx, sy), (dx, dy)):
##                                return True
        return False

    def gameover(self):
        self.ingame = False
        self.draw()
        screen = self.screen
        if self.check:
            message1 = 'Checkmate'
            message2 = '%s Player Wins' % ('White', 'Black')[1 - self.turn]
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

    def draw(self):
        screen = self.screen
        screen.fill(BGCOLOR)

        self.draw_board()

        if self.selected:
            if self.in_promotion:
                self.highlight(*self.selected, PROMOTE_COLOR)
            else:
                for x, y in self.enum_moves(*self.selected):
                    self.highlight(x, y, MOVE_COLOR)
                self.highlight(*self.selected, SELECT_COLOR)

        if self.in_promotion:
            self.draw_promotion()
        else:
            text = '%s Turn' % ('White', 'Black')[self.turn]
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


class Piece:
    def __init__(self, side, type):
        self.side = side
        self.type = type
        self.image = Game.piece_images[side][type]

    def __repr__(self):
        return 'Piece({}, {})'.format(
            ('WHITE', 'BLACK')[self.side],
            ('PAWN', 'ROOK', 'KNIGHT', 'BISHOP', 'QUEEN', 'KING')[self.type])

    def can_move(self, src, dest, board):
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


if __name__ == '__main__':
    try:
        game = Game()
        game.run()
    finally:
        pg.quit()
