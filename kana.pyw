import enum
import random
import unicodedata

import pygame as pg
from pygame.font import SysFont

WIDTH = 640
HEIGHT = 480
FPS = 30

BGCOLOR = (192, 224, 255)
FGCOLOR = (0, 0, 0)
WRONGCOLOR = (255, 0, 0)
SCORECOLOR = (0, 64, 255)
FAILURESCOLOR = (255, 0, 0)
SUCCESSESCOLOR = (0, 192, 0)
HOVERCOLOR = (0, 255, 255)
CLICKCOLOR = (0, 192, 255)

NCHOICES = 5

JAP_FONT = 'MS Gothic'
LATIN_FONT = 'Arial'
TITLE_FONT = 'Verdana'

class Mode(enum.Enum):
    KANA_TO_LATIN = 1
    LATIN_TO_KANA = 2

class Charset(enum.Enum):
    HIRAGANA = 1
    KATAKANA = 2

#region data

def nospace(s):
    return ''.join(s.split())

HIRAGANA_CHARS = nospace('''
あいうえお
かきくけこ
さしすせそ
たちつてと
なにぬねの
はひふへほ
まみむめも
や　ゆ　よ
らりるれろ
わ　　　を
ん
''')

HIRAGANA_EXT_CHARS = nospace('''
がぎぐげご
ざじずぜぞ
だぢづでど
ばびぶべぼ
ぱぴぷぺぽ
''')

KATAKANA_CHARS = nospace('''
アイウエオ
カキクケコ
サシスセソ
タチツテト
ナニヌネノ
ハヒフヘホ
マミムメモ
ヤ　ユ　ヨ
ラリルレロ
ワ　　　ヲ
ン
''')

KATAKANA_EXT_CHARS = nospace('''
ガギグゲゴ
ザジズゼゾ
ダヂヅデド
バビブベボ
パピプペポ
''')

#endregion

CHARSETS = {
    Charset.HIRAGANA: HIRAGANA_CHARS,
    Charset.KATAKANA: KATAKANA_CHARS,
}

IRREGULAR = {
    'si': 'shi', 'ti': 'chi', 'tu': 'tsu', 'hu': 'fu',
    'zi': 'ji', 'di': 'ji', 'du': 'zu'
}

def kana_name(c):
    name = unicodedata.name(c).split()[-1].lower()
    return IRREGULAR.get(name, name)


def make_rect(size=(0, 0), **kwargs):
    r = pg.Rect((0, 0), size)
    for k, v in kwargs.items():
        setattr(r, k, v)
    return r

def center_rect(center, size):
    r = pg.Rect((0, 0), size)
    r.center = center
    return r


class Label:
    def __init__(self, text, rect, font=None, text_color=(0, 0, 0), bg_color=None,
                 border_width=0, border_radius=0, border_color=(0, 0, 0),
                 hover_color=None, click_color=None, visible=True, enabled=True,
                 on_click=None):
        self.text = text
        self.font: pg.font.Font = font or SysFont(LATIN_FONT, 20)
        if len(rect) == 2:
            size = self.font.size(text)
            self.rect = center_rect(rect, size)
        else:
            self.rect = pg.Rect(rect)
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.border_color = border_color
        self.hover_color = hover_color
        self.click_color = click_color
        self.visible = visible
        self.enabled = enabled
        self.on_click = on_click
        self.hovering = False
        self.clicking = False

    def mouse_down(self, x, y):
        if self.enabled and self.rect.collidepoint(x, y):
            self.clicking = True

    def mouse_up(self, x, y):
        if self.enabled and self.clicking and self.rect.collidepoint(x, y):
            if self.on_click:
                self.on_click(self)
        self.clicking = False

    def hover(self, x, y):
        self.hovering = self.rect.collidepoint(x, y)

    def draw(self, screen):
        if not self.visible:
            return
        bg_color = (self.click_color if self.clicking and self.click_color
                    else self.hover_color if self.hovering and self.hover_color
                    else self.bg_color)
        if bg_color:
            pg.draw.rect(screen, bg_color, self.rect, 0,
                         self.border_radius)
        text_img = self.font.render(self.text, True, self.text_color)
        text_rect = text_img.get_rect(center=self.rect.center)
        screen.blit(text_img, text_rect)
        if self.border_width:
            pg.draw.rect(screen, self.border_color, self.rect,
                         self.border_width, self.border_radius)


class Button(Label):
    def __init__(self, text, rect, font, text_color=(0, 0, 0), bg_color=None,
                 border_width=2, border_radius=5, border_color=(0, 0, 0),
                 hover_color=None, click_color=None, visible=True, enabled=True,
                 on_click=None):
        super().__init__(text, rect, font, text_color, bg_color, border_width,
                         border_radius, border_color, hover_color, click_color,
                         visible, enabled, on_click)


class Scene:
    def __init__(self, game: 'Game'):
        self.game = game
        self.labels: list[Label] = []

    def event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            for lbl in self.labels:
                lbl.mouse_down(*event.pos)
        elif event.type == pg.MOUSEBUTTONUP:
            for lbl in self.labels:
                lbl.mouse_up(*event.pos)
        elif event.type == pg.MOUSEMOTION:
            for lbl in self.labels:
                lbl.hover(*event.pos)

    def update(self):
        pass

    def draw(self, screen):
        for lbl in self.labels:
            lbl.draw(screen)


class StartScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.mode = Mode.KANA_TO_LATIN
        self.charset = Charset.HIRAGANA
        self.setup_ui()

    def setup_ui(self):
        main_label = Label('Kana/仮名', (WIDTH//2, HEIGHT//2-110),
                           SysFont(JAP_FONT, 60))
        mode_button1 = Button(
            'Kana→Latin', center_rect((WIDTH//2 - 80, HEIGHT//2 - 10), (130, 50)),
            SysFont(LATIN_FONT, 24), hover_color=(64, 128, 255),
            on_click=lambda b: self.set_mode(Mode.KANA_TO_LATIN))
        mode_button2 = Button(
            'Latin→Kana', center_rect((WIDTH//2 + 80, HEIGHT//2 - 10), (130, 50)),
            SysFont(LATIN_FONT, 24), hover_color=(64, 128, 255),
            on_click=lambda b: self.set_mode(Mode.LATIN_TO_KANA))
        self.mode_buttons = {Mode.KANA_TO_LATIN: mode_button1,
                             Mode.LATIN_TO_KANA: mode_button2}
        charset_button1 = Button(
            'Hiragana', center_rect((WIDTH//2 - 80, HEIGHT//2 + 50), (130, 50)),
            SysFont(LATIN_FONT, 24), hover_color=(64, 128, 255),
            on_click=lambda b: self.set_charset(Charset.HIRAGANA))
        charset_button2 = Button(
            'Katakana', center_rect((WIDTH//2 + 80, HEIGHT//2 + 50), (130, 50)),
            SysFont(LATIN_FONT, 24), hover_color=(64, 128, 255),
            on_click=lambda b: self.set_charset(Charset.KATAKANA))
        self.charset_buttons = {Charset.HIRAGANA: charset_button1,
                                Charset.KATAKANA: charset_button2}
        start_button = Button(
            'Start', center_rect((WIDTH//2, HEIGHT//2 + 150), (150, 80)),
            SysFont(TITLE_FONT, 50), bg_color=(0, 255, 255),
            hover_color=(64, 128, 255), on_click=self.start)
        self.mode_lbl = Label('', (100, 50), visible=False)
        self.charset_lbl = Label('<>', (200, 50), visible=False)
        self.labels = [
            main_label, mode_button1, mode_button2, charset_button1,
            charset_button2, self.mode_lbl, self.charset_lbl, start_button
        ]

    def set_mode(self, mode):
        self.mode = mode

    def set_charset(self, charset):
        self.charset = charset

    def start(self, button):
        self.game.change_scene(GameScene(self.game, self.charset, self.mode))

    def update(self):
        self.mode_lbl.text = self.mode.name
        self.charset_lbl.text = self.charset
        for mode, button in self.mode_buttons.items():
            if mode == self.mode:
                button.bg_color = (0, 192, 255)
            else:
                button.bg_color = (192, 192, 255)
        for charset, button in self.charset_buttons.items():
            if charset == self.charset:
                button.bg_color = (0, 192, 255)
            else:
                button.bg_color = (192, 192, 255)

    def draw(self, screen):
        screen.fill(BGCOLOR)
        super().draw(screen)


class GameScene(Scene):
    def __init__(self, game, charset=Charset.HIRAGANA, mode=Mode.KANA_TO_LATIN):
        super().__init__(game)
        self.charset = CHARSETS[charset]
        self.charset_trans = list(set(map(kana_name, self.charset)))
        self.mode = mode
        self.current_char = ''
        self.choices = []
        self.running = False
        self.score = 0
        self.successes = 0
        self.failures = 0

        self.setup_ui()
        self.next_round()

    def setup_ui(self):
        if self.mode == Mode.KANA_TO_LATIN:
            char_font = SysFont(JAP_FONT, 100)
            choice_font = SysFont(LATIN_FONT, 48)
        else:
            char_font = SysFont(LATIN_FONT, 100)
            choice_font = SysFont(JAP_FONT, 48)

        self.char_lbl = Label('', (WIDTH//2, HEIGHT//2 - 50), char_font)

        self.choice_buttons: list[Label] = []
        for i in range(NCHOICES):
            x = int(WIDTH/2 + 100*(i - (NCHOICES - 1) / 2))
            y = HEIGHT//2 + 100
            but = Button('', center_rect((x, y), (65, 60)), choice_font,
                         hover_color=HOVERCOLOR, click_color=CLICKCOLOR)
            self.choice_buttons.append(but)

        self.wrong_lbl = Label('WRONG', (WIDTH//2, HEIGHT//2 + 180),
                               SysFont(LATIN_FONT, 48), WRONGCOLOR,
                               visible=False)

        self.score_lbl = Label(str(self.score), (50, 50),
                               SysFont(LATIN_FONT, 48), SCORECOLOR)
        self.successes_lbl = Label(str(self.successes), (100, 50),
                                   SysFont(LATIN_FONT, 48), SUCCESSESCOLOR)
        self.failures_lbl = Label(str(self.failures), (150, 50),
                                  SysFont(LATIN_FONT, 48), FAILURESCOLOR)

        self.labels = [self.char_lbl, *self.choice_buttons, self.wrong_lbl,
                       self.score_lbl, self.successes_lbl, self.failures_lbl]

    def next_round(self):
        self.current_char = char = random.choice(self.charset)
        char_trans = kana_name(char)
        if self.mode == Mode.KANA_TO_LATIN:
            lbl_text = char
            right_choice = char_trans
            others = [c for c in self.charset_trans if c != char_trans]
        else:
            lbl_text = char_trans
            right_choice = char
            others = [c for c in self.charset if kana_name(c) != char_trans]
        self.choices = choices = random.sample(others, NCHOICES-1)
        choices.append(right_choice)
        random.shuffle(choices)

        self.wrong_lbl.visible = False
        self.char_lbl.text = lbl_text
        for but, choice in zip(self.choice_buttons, choices):
            but.text = choice
            but.on_click = (self.handle_right if choice == right_choice
                            else self.handle_wrong)
            but.bg_color = None
            but.hover_color = HOVERCOLOR
            but.enabled = True

    def handle_right(self, button):
        # print('correct')
        self.score += 1
        self.successes += 1
        self.next_round()

    def handle_wrong(self, button):
        # print('wrong')
        self.score -= 1
        self.failures += 1
        self.wrong_lbl.visible = True
        button.bg_color = WRONGCOLOR
        button.hover_color = None
        button.enabled = False

    def update(self):
        self.score_lbl.text = str(self.score)
        self.successes_lbl.text = str(self.successes)
        self.failures_lbl.text = str(self.failures)

    def draw(self, screen):
        screen.fill(BGCOLOR)
        super().draw(screen)


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.scene: Scene = None
        self.next_scene: Scene = None
        self.change_scene(StartScene(self))

    def main(self):
        self.running = True
        clock = pg.time.Clock()
        while self.running:
            self.scene = self.next_scene
            self.events()
            self.update()
            self.draw()
            clock.tick(FPS)

    def change_scene(self, scene: Scene):
        self.next_scene = scene
    
    def quit(self):
        self.running = False

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
                continue
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_F4 and event.mod & pg.KMOD_ALT:
                    self.quit()
                    continue
                elif event.key == pg.K_ESCAPE:
                    if isinstance(self.scene, StartScene):
                        self.quit()
                    else:
                        self.change_scene(StartScene(self))
            self.scene.event(event)

    def update(self):
        self.scene.update()

    def draw(self):
        self.scene.draw(self.screen)
        pg.display.flip()


if __name__ == '__main__':
    try:
        Game().main()
    finally:
        pg.quit()
