#!/usr/bin/env python3
import sys, os
import pygame as pg

DIR = os.path.dirname(sys.argv[0])
FONTFILE = os.path.join(DIR, 'data', 'old-english-text-mt.ttf')

# Dimensions
XMARG = 48
YMARG = 72
SQSIZE = 48
BSIZE = SQSIZE * 8
WIDTH = BSIZE + XMARG*2 # 480
HEIGHT = BSIZE + YMARG*2 # 528

# Colors
BGCOLOR = (128, 128, 128)
BCOLOR = (0, 0, 0)
WCOLOR = (255, 255, 255)
SELCOLOR = (0, 255, 255)
PROMCOLOR = (0, 255, 255)
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
    path = os.path.join(DIR, 'images', name + '.png')
    img = pg.image.load(path)
    if convert:
        img = img.convert_alpha()
    return img

def grid2pix(x, y):
    return x*SQSIZE + XMARG, (7 - y)*SQSIZE + YMARG

def pix2grid(px, py):
    return (px - XMARG)//SQSIZE, 7 - (py - YMARG)//SQSIZE


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
        self.run()

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
        for x in range(8):
            for y in range(8):
                color = (BCOLOR, WCOLOR)[(x + y) % 2]
                px, py = grid2pix(x, y)
                pg.draw.rect(screen, color, (px, py, SQSIZE, SQSIZE))
                piece = self.board[x][y]
                if piece:
                    screen.blit(piece.image, (px, py))

        rect = self.title_image.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(self.title_image, rect)
        pg.display.flip()

    def setup_board(self):
        self.board = board = [[None] * 8 for i in range(8)]
        order = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for x, type in enumerate(order):
            board[x][0] = Piece(WHITE, type)
            board[x][7] = Piece(BLACK, type)
        for x in range(8):
            board[x][1] = Piece(WHITE, PAWN)
            board[x][6] = Piece(BLACK, PAWN)
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
        if 0 < HEIGHT - (YMARG - SQSIZE)//2 - py <= SQSIZE:
            i = (px - XMARG) // SQSIZE - 2
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

    def move_is_check(self, src, dest):
        board = self.board
        (sx, sy), (dx, dy) = src, dest
        src_piece = board[sx][sy]
        dest_piece = board[dx][dy]
        board[sx][sy] = None
        board[dx][dy] = src_piece
        check = self.is_check()
        board[sx][sy] = src_piece
        board[dx][dy] = dest_piece
        return check

    def is_check(self):
        board = self.board
        for x in range(8):
            for y in range(8):
                piece = board[x][y]
                if piece and piece.type == KING and piece.side == self.turn:
                    king_pos = (x, y)
                    break
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
        for sx in range(8):
            for sy in range(8):
                piece = self.board[sx][sy]
                if piece and piece.side == self.turn:
                    for dx in range(8):
                        for dy in range(8):
                            if self.can_move((sx, sy), (dx, dy)):
                                return True
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

    def draw(self):
        screen = self.screen
        screen.fill(BGCOLOR)

        for x in range(8):
            for y in range(8):
                color = (BCOLOR, WCOLOR)[(x + y) % 2]
                px, py = grid2pix(x, y)
                pg.draw.rect(screen, color, (px, py, SQSIZE, SQSIZE))
                piece = self.board[x][y]
                if piece:
                    screen.blit(piece.image, (px, py))

        if self.selected:
            sx, sy = grid2pix(*self.selected)
            color = PROMCOLOR if self.in_promotion else SELCOLOR
            pg.draw.rect(screen, color, (sx, sy, SQSIZE, SQSIZE), 2)

        if self.in_promotion:
            for i in range(4):
                color = (WCOLOR, BCOLOR)[i % 2]
                px, py = XMARG + SQSIZE * (i + 2), HEIGHT - (YMARG + SQSIZE)//2
                pg.draw.rect(screen, color, (px, py, SQSIZE, SQSIZE))
                typ = [QUEEN, KNIGHT, ROOK, BISHOP][i]
                screen.blit(self.piece_images[self.turn][typ], (px, py))
            txtimg = self.font1.render('Choose Promotion', True, TXTCOLOR)
            rect = txtimg.get_rect(center=(WIDTH//2, YMARG//2))
            screen.blit(txtimg, rect)

        else:
            text = '%s Turn' % ('White', 'Black')[self.turn]
            txtimg = self.font1.render(text, True, TXTCOLOR)
            rect = txtimg.get_rect(center=(WIDTH//2, YMARG//2))
            screen.blit(txtimg, rect)
            if self.check:
                txtimg = self.font1.render('Check', True, TXTCOLOR)
                rect = txtimg.get_rect(center=(WIDTH//2, HEIGHT - YMARG//2))
                screen.blit(txtimg, rect)


class Piece:
    def __init__(self, side, type):
        self.side = side
        self.type = type
        self.image = Game.piece_images[side][type]

    def can_move(self, src, dest, board):
        type = self.type
        x1, y1 = src
        x2, y2 = dest
        dx, dy = x2 - x1, y2 - y1
        sx = dx and dx // abs(dx)
        sy = dy and dy // abs(dy)

        if type == PAWN:
            firstmove = y1 == (1, 6)[self.side] # (WHITE, BLACK)
            dir = (1, -1)[self.side]
            dest_piece = board[x2][y2]
            if firstmove and dx == 0 and dy == 2*dir:
                return not (dest_piece or board[x1][y1 + dir])
            elif dy == dir:
                return (dx == 0 and not dest_piece or
                        abs(dx) == 1 and dest_piece)

        elif type == ROOK:
            if dx == 0:
                return not any(board[x1][y] for y in range(y1+sy, y2, sy))
            if dy == 0:
                return not any(board[x][y1] for x in range(x1+sx, x2, sx))

        elif type == KNIGHT:
            return (abs(dx) == 2 and abs(dy) == 1 or
                    abs(dx) == 1 and abs(dy) == 2)

        elif type == BISHOP:
            if abs(dx) == abs(dy):
                return not any(board[x][y] for (x, y) in
                    zip(range(x1+sx, x2, sx), range(y1+sy, y2, sy)))

        elif type == QUEEN:
            if dx == 0:
                return not any(board[x1][y] for y in range(y1+sy, y2, sy))
            if dy == 0:
                return not any(board[x][y1] for x in range(x1+sx, x2, sx))
            if abs(dx) == abs(dy):
                return not any(board[x][y] for (x, y) in
                    zip(range(x1+sx, x2, sx), range(y1+sy, y2, sy)))

        elif type == KING:
            return max(abs(dx), abs(dy)) == 1

        return False


if __name__ == '__main__':
    try:
        game = Game()
    finally:
        pg.quit()
