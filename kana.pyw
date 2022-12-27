import sys
import random
import unicodedata
import pygame as pg

WIDTH = 640
HEIGHT = 480
BGCOLOR = (192, 224, 255)
FGCOLOR = (0, 0, 0)
WRONGCOLOR = (255, 0, 0)
SCORECOLOR = (0, 64, 255)
BADSCORECOLOR = (255, 0, 0)
HOVERCOLOR = (0, 255, 255)
FPS = 30
NCHOICES = 5
KANA_TO_ROMAN = 1
ROMAN_TO_KANA = 2

def nospace(s):
    return ''.join(s.split())

HIRAGANA = nospace('''
あかさたなはまやらわん
いきしちにひみ　り
うくすつぬふむゆる
えけせてねへめ　れ
おこそとのほもよろを
''')

HIRAGANA_EXT = nospace('''
がざだばぱ
ぎじぢびぴ
ぐずづぶぷ
げぜでべぺ
ごぞどぼぽ
''')

KATAKANA = nospace('''
アカサタナハマヤラワン
イキシチニヒミ　リ
ウクスツヌフムユル
エケセテネヘメ　レ
オコソトノホモヨロヲ
''')

KATAKANA_EXT = nospace('''
ガザダバパ
ギジヂビピ
グズヅブプ
ゲゼデベペ
ゴゾドボポ
''')

IRREGULAR = {'si': 'shi', 'ti': 'chi', 'tu': 'tsu', 'hu': 'fu',
             'zi': 'ji', 'di': 'ji', 'du': 'zu'}

charsets = {'hiragana': HIRAGANA, 'hiragana-ext': HIRAGANA_EXT,
            'hiragana-all': HIRAGANA + HIRAGANA_EXT,
            'katakana': KATAKANA, 'katakana-ext': KATAKANA_EXT,
            'katakana-all': KATAKANA + KATAKANA_EXT,
            'all': HIRAGANA + HIRAGANA_EXT + KATAKANA + KATAKANA_EXT}

def kana_name(c):
    name = unicodedata.name(c).split()[-1].lower()
    return IRREGULAR.get(name, name)

class Game:
    def __init__(self, charset='hiragana', mode=KANA_TO_ROMAN):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.jap_font_big = pg.font.SysFont('MS Gothic', 100)
        self.jap_font_small = pg.font.SysFont('MS Gothic', 48)
        self.roman_font_big = pg.font.SysFont('Arial', 100)
        self.roman_font_small = pg.font.SysFont('Arial', 48)
        self.charset = ''.join(charsets[s.lower()] for s in charset.split('+'))
        self.char = ''
        self.choices = []
        self.running = False
        self.show_wrong = False
        self.score = 0
        self.hover_button = None
        self.mode = mode
        self.next_char()

    def main(self):
        self.running = True
        clock = pg.time.Clock()
        while self.running:
            self.events()
            self.update()
            self.draw()
            clock.tick(FPS)

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if (event.key == pg.K_ESCAPE or
                    event.key == pg.K_F4 and event.mod & pg.KMOD_ALT):
                    self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.click(*event.pos)
            elif event.type == pg.MOUSEMOTION:
                self.hover_button = self.mouse_button_index(*event.pos)

    def update(self):
        pass

    def draw(self):
        self.screen.fill(BGCOLOR)
        char_font = self.jap_font_big if mode == KANA_TO_ROMAN else self.roman_font_big
        char_str = self.char if mode == KANA_TO_ROMAN else kana_name(self.char)
        char_img = char_font.render(char_str, True, FGCOLOR)
        char_rect = char_img.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        self.screen.blit(char_img, char_rect)
        choice_font = self.roman_font_small if mode == KANA_TO_ROMAN else self.jap_font_small
        for i, (choice, rect) in enumerate(zip(self.choices, self.choice_rects())):
            if i == self.hover_button:
                pg.draw.rect(self.screen, HOVERCOLOR, rect, 0, 5)
            choice_str = kana_name(choice) if mode == KANA_TO_ROMAN else choice
            choice_img = choice_font.render(choice_str, True, FGCOLOR)
            choice_img_rect = choice_img.get_rect(center=rect.center)
            self.screen.blit(choice_img, choice_img_rect)
            pg.draw.rect(self.screen, FGCOLOR, rect, 2, 5)
        if self.show_wrong:
            label_img = self.roman_font_small.render('WRONG', True, WRONGCOLOR)
            label_rect = label_img.get_rect(center=(WIDTH//2, HEIGHT//2 + 180))
            self.screen.blit(label_img, label_rect)
        score_color = SCORECOLOR if self.score >=0 else BADSCORECOLOR
        score_img = self.roman_font_small.render(str(self.score), True, score_color)
        score_rect = score_img.get_rect(center=(50, 50))
        self.screen.blit(score_img, score_rect)
        pg.display.flip()

    def click(self, x, y):
        i = self.mouse_button_index(x, y)
        if i is not None:
            if self.choices[i] == self.char:
                self.handle_right()
            else:
                self.handle_wrong()

    def mouse_button_index(self, x, y):
        for i, rect in enumerate(self.choice_rects()):
            if rect.collidepoint(x, y):
                return i
        return None

    def handle_right(self):
        # print('correct')
        self.score += 1
        self.next_char()

    def handle_wrong(self):
        # print('wrong')
        self.score -= 1
        self.show_wrong = True

    def next_char(self):
        self.char = random.choice(self.charset)
        other_chars = list(set(self.charset) - {self.char})
        choices = random.sample(other_chars, NCHOICES-1)
        choices.append(self.char)
        random.shuffle(choices)
        self.choices = choices
        self.show_wrong = False

    def choice_rects(self) -> list[pg.Rect]:
        rects = []
        for i, choice in enumerate(self.choices):
            x = int(WIDTH/2 + 100*(i - (NCHOICES - 1) / 2))
            y = HEIGHT//2 + 100
            rect = pg.Rect(0, 0, 60, 55)
            rect.center = (x, y)
            rects.append(rect)
        return rects


if __name__ == '__main__':
    charset = sys.argv[1] if len(sys.argv) > 1 else 'hiragana'
    mode = int(sys.argv[2]) if len(sys.argv) > 2 else KANA_TO_ROMAN
    try:
        Game(charset).main()
    finally:
        pg.quit()
