#!/usr/bin/python3
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
NTRIES = 5

JAP_FONT = ['MS Gothic', 'notosanscjkjp']
LATIN_FONT = ['arialnarrow', 'Arial']
TITLE_FONT = 'Verdana'

class Mode(enum.Enum):
    KANA_TO_LATIN = 1
    LATIN_TO_KANA = 2
    KANA_TO_LATIN_TEXT = 3

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


def mkrect(rect_or_size=(0, 0), **kwargs):
    if len(rect_or_size) == 4:
        r = pg.Rect(rect_or_size)
    else:
        r = pg.Rect((0, 0), rect_or_size)
    for k, v in kwargs.items():
        setattr(r, k, v)
    return r

def crect(center, size):
    r = pg.Rect((0, 0), size)
    r.center = center
    return r


class Widget:
    def draw(self, screen: pg.Surface):
        pass

    def event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            self.mouse_down(event)
        elif event.type == pg.MOUSEBUTTONUP:
            self.mouse_up(event)
        elif event.type == pg.MOUSEMOTION:
            self.mouse_move(event)
        elif event.type == pg.KEYDOWN:
            self.key_down(event)
        elif event.type == pg.KEYUP:
            self.key_up(event)

    def mouse_down(self, event: pg.event.Event):
        pass

    def mouse_up(self, event: pg.event.Event):
        pass

    def mouse_move(self, event: pg.event.Event):
        pass

    def key_down(self, event: pg.event.Event):
        pass

    def key_up(self, event: pg.event.Event):
        pass


class Label(Widget):
    def __init__(self, text: str, rect, font=None, *, text_color=(0, 0, 0),
                 bg_color=None, border_width=0, border_radius=0,
                 border_color=(0, 0, 0), hover_color=None, click_color=None,
                 select_color=None, disabled_color=None, selected=False,
                 visible=True, enabled=True, data=None, on_click=None):
        self.text = text
        self.font: pg.font.Font = font or SysFont(LATIN_FONT, 24)
        if len(rect) == 2:
            size = self.font.size(text)
            self.rect = crect(rect, size)
        else:
            self.rect = pg.Rect(rect)
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.border_color = border_color
        self.hover_color = hover_color
        self.click_color = click_color
        self.select_color = select_color
        self.disabled_color = disabled_color
        self.selected = selected
        self.visible = visible
        self.enabled = enabled
        self.data = data
        self.on_click = on_click
        self.hovering = False
        self.clicking = False

    def mouse_down(self, event):
        if self.enabled and self.rect.collidepoint(event.pos):
            self.clicking = True

    def mouse_up(self, event):
        if self.enabled and self.clicking and self.rect.collidepoint(event.pos):
            if self.on_click:
                self.on_click(self)
        self.clicking = False

    def mouse_move(self, event):
        self.hovering = self.rect.collidepoint(event.pos)

    def toggle_select(self):
        self.selected = not self.selected

    def get_bg_color(self):
        return (self.disabled_color if not self.enabled and self.disabled_color
                else self.click_color if self.clicking and self.click_color
                else self.hover_color if self.hovering and self.hover_color
                else self.select_color if self.selected and self.select_color
                else self.bg_color)

    def get_text(self):
        return self.text

    def text_rect(self):
        return crect(self.rect.center, self.font.size(self.get_text()))

    def draw(self, screen):
        if not self.visible:
            return
        bg_color = self.get_bg_color()
        if bg_color:
            pg.draw.rect(screen, bg_color, self.rect, 0,
                         self.border_radius)
        text_img = self.font.render(self.get_text(), True, self.text_color)
        text_rect = text_img.get_rect(center=self.rect.center)
        screen.blit(text_img, text_rect)
        if self.border_width:
            pg.draw.rect(screen, self.border_color, self.rect,
                         self.border_width, self.border_radius)


class Button(Label):
    def __init__(self, text: str, rect, font=None, *, border_width=2,
                 border_radius=5, **kwargs):
        super().__init__(text, rect, font, border_width=border_width,
                         border_radius=border_radius, **kwargs)


class TextBox(Label):
    def __init__(self, text: str, rect, font=None, *, on_enter=None,
                 border_width=2, **kwargs):
        super().__init__(text, rect, font, border_width=border_width, **kwargs)
        self.on_enter = on_enter

    def clear(self):
        self.text = ''

    def key_down(self, event):
        if not self.enabled:
            return
        if event.key == pg.K_RETURN:
            if self.on_enter:
                self.on_enter(self)
        elif event.key == pg.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.unicode and event.unicode.isprintable():
            self.text += event.unicode

    def draw(self, screen):
        super().draw(screen)
        if pg.time.get_ticks() % 1000 > 500:
            bar_img = self.font.render('|', True, self.text_color)
            text_rect = self.text_rect()
            bar_rect = bar_img.get_rect(midleft=text_rect.midright)
            screen.blit(bar_img, bar_rect)


class Scene(Widget):
    def __init__(self, game: 'Game'):
        self.game = game
        self.widgets: list[Widget] = []
        self.bg_color = BGCOLOR

    def event(self, event: pg.event.Event):
        for w in self.widgets:
            if w.event(event):
                return
        super().event(event)

    def add(self, widget: Widget):
        self.widgets.append(widget)
        return widget

    def update(self):
        pass

    def draw_bg(self, screen: pg.Surface):
        screen.fill(self.bg_color)

    def draw_widgets(self, screen: pg.Surface):
        for w in self.widgets:
            w.draw(screen)

    def draw(self, screen: pg.Surface):
        self.draw_bg(screen)
        self.draw_widgets(screen)


class StartScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.mode = Mode.KANA_TO_LATIN
        self.charset = Charset.HIRAGANA
        self.init_ui()

    def init_ui(self):
        main_label = Label('Kana/仮名', (WIDTH//2, HEIGHT//2-110),
                           SysFont(JAP_FONT, 60))
        style = {
            'font': SysFont(LATIN_FONT, 24),
            'bg_color': (192, 192, 255),
            'select_color': (0, 192, 255),
            'hover_color': (64, 128, 255),
        }
        mode_button1 = Button(
            'Kana→Latin', crect((WIDTH//2 - 150, HEIGHT//2 - 15), (130, 50)),
            on_click=self.handle_set_mode, data=Mode.KANA_TO_LATIN, **style)
        mode_button2 = Button(
            'Latin→Kana', crect((WIDTH//2, HEIGHT//2 - 15), (130, 50)),
            on_click=self.handle_set_mode, data=Mode.LATIN_TO_KANA, **style)
        mode_button3 = Button(
            'Kana→Free', crect((WIDTH//2 + 150, HEIGHT//2 - 15), (130, 50)),
            on_click=self.handle_set_mode, data=Mode.KANA_TO_LATIN_TEXT, **style)
        self.mode_buttons = [mode_button1, mode_button2, mode_button3]

        charset_button1 = Button(
            'Hiragana', crect((WIDTH//2 - 80, HEIGHT//2 + 55), (130, 50)),
            on_click=self.handle_set_charset, data=Charset.HIRAGANA, **style)
        charset_button2 = Button(
            'Katakana', crect((WIDTH//2 + 80, HEIGHT//2 + 55), (130, 50)),
            on_click=self.handle_set_charset, data=Charset.KATAKANA, **style)
        self.charset_buttons = [charset_button1, charset_button2]

        start_button = Button(
            'Start', crect((WIDTH//2, HEIGHT//2 + 150), (150, 80)),
            SysFont(TITLE_FONT, 50), bg_color=(0, 255, 255),
            hover_color=(64, 128, 255), on_click=self.handle_start)

        self.mode_lbl = Label('', (100, 50), visible=False)
        self.charset_lbl = Label('', (200, 50), visible=False)

        self.widgets = [
            main_label, *self.mode_buttons, *self.charset_buttons,
            self.mode_lbl, self.charset_lbl, start_button,
        ]

    def handle_set_mode(self, button: Button):
        self.mode = button.data

    def handle_set_charset(self, button: Button):
        self.charset = button.data

    def handle_start(self, button):
        self.game.change_scene(GameScene, self.charset, self.mode)

    def update(self):
        self.mode_lbl.text = self.mode.name
        self.charset_lbl.text = self.charset
        for button in self.mode_buttons:
            button.selected = button.data == self.mode
        for button in self.charset_buttons:
            button.selected = button.data == self.charset

    def key_down(self, event: pg.event.Event):
        if event.key == pg.K_ESCAPE:
            self.game.quit()


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
        self.cur_failures = 0

        self.init_ui()
        self.next_round()

    def init_ui(self):
        latin_font_48 = SysFont(LATIN_FONT, 48)
        if self.mode == Mode.LATIN_TO_KANA:
            char_font = SysFont(LATIN_FONT, 100)
            choice_font = SysFont(JAP_FONT, 48)
        else:
            char_font = SysFont(JAP_FONT, 100)
            choice_font = latin_font_48

        self.char_lbl = Label('', (WIDTH//2, HEIGHT//2 - 50), char_font)

        if self.mode == Mode.KANA_TO_LATIN_TEXT:
            tb_rect = crect((WIDTH//2, HEIGHT//2 + 100), (150, 60))
            self.answer_enter = TextBox('', tb_rect, SysFont(LATIN_FONT, 42),
                                        on_enter=self.handle_text_enter)
            skip_rect = mkrect((100, 50), left=tb_rect.right + 20,
                               centery=tb_rect.centery)
            self.skip_button = Button(
                'Skip', skip_rect, bg_color=(255, 128, 0),
                hover_color=(255, 0, 0), click_color=(128, 0, 0),
                on_click=self.skip)
            answer_widgets = [self.answer_enter, self.skip_button]
        else:
            self.choice_buttons: list[Button] = []
            for i in range(NCHOICES):
                x = int(WIDTH/2 + 100*(i - (NCHOICES - 1) / 2))
                y = HEIGHT//2 + 100
                but = Button('', crect((x, y), (65, 60)), choice_font,
                             hover_color=HOVERCOLOR, click_color=CLICKCOLOR,
                             disabled_color=WRONGCOLOR,
                             on_click=self.handle_choice)
                self.choice_buttons.append(but)
            answer_widgets = [*self.choice_buttons]

        self.wrong_lbl = Label('WRONG', (WIDTH//2, HEIGHT//2 + 180),
                               latin_font_48, text_color=WRONGCOLOR,
                               visible=False)

        self.score_lbl = Label(str(self.score), (50, 50),
                               latin_font_48, text_color=SCORECOLOR)
        self.successes_lbl = Label(str(self.successes), (110, 50),
                                   latin_font_48, text_color=SUCCESSESCOLOR)
        self.failures_lbl = Label(str(self.failures), (170, 50),
                                  latin_font_48, text_color=FAILURESCOLOR)

        self.widgets = [
            self.char_lbl, *answer_widgets, self.wrong_lbl,
            self.score_lbl, self.successes_lbl, self.failures_lbl
        ]

    def next_round(self):
        self.current_char = char = random.choice(self.charset)
        char_trans = kana_name(char)
        if self.mode == Mode.LATIN_TO_KANA:
            lbl_text = char_trans
            right_choice = self.right_choice = char
            others = [c for c in self.charset if kana_name(c) != char_trans]
        else:
            lbl_text = char
            right_choice = self.right_choice = char_trans
            others = [c for c in self.charset_trans if c != char_trans]

        self.wrong_lbl.visible = False
        self.char_lbl.text = lbl_text

        if self.mode == Mode.KANA_TO_LATIN_TEXT:
            self.answer_enter.clear()
        else:
            choices = self.choices = random.sample(others, NCHOICES-1)
            choices.append(right_choice)
            random.shuffle(choices)

            for but, choice in zip(self.choice_buttons, choices):
                but.text = but.data = choice
                but.enabled = True

        self.cur_failures = 0

    def handle_text_enter(self, textbox: TextBox):
        if textbox.text == self.right_choice:
            self.handle_right()
        else:
            self.handle_wrong()
            if self.cur_failures >= NTRIES:
                self.skip()
            else:
                textbox.clear()

    def handle_choice(self, button: Button):
        if button.data == self.right_choice:
            self.handle_right()
        else:
            self.handle_wrong()

    def handle_right(self, button=None):
        # print('correct')
        self.score += 1
        self.successes += 1
        self.next_round()

    def handle_wrong(self, button: Button = None):
        # print('wrong')
        self.score -= 1
        self.failures += 1
        self.cur_failures += 1
        self.wrong_lbl.visible = True
        if button:
            button.enabled = False

    def skip(self, button=None):
        self.answer_enter.text = self.right_choice
        failures = max(NTRIES - self.cur_failures, 0)
        self.score -= failures
        self.failures += failures

    def update(self):
        self.score_lbl.text = str(self.score)
        self.successes_lbl.text = str(self.successes)
        self.failures_lbl.text = str(self.failures)

    def key_down(self, event: pg.event.Event):
        if event.key == pg.K_ESCAPE:
            self.game.change_scene(StartScene)


class Game:
    def __init__(self):
        pg.init()
        pg.key.set_repeat(500, 60)
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption('Kana/仮名')
        self.scene: Scene = None
        self.next_scene: Scene = None
        self.change_scene(StartScene)

    def main(self):
        self.running = True
        clock = pg.time.Clock()
        while self.running:
            self.scene = self.next_scene
            self.events()
            self.update()
            self.draw()
            clock.tick(FPS)

    def change_scene(self, scene_class: type[Scene], *args, **kwargs):
        self.next_scene = scene_class(self, *args, **kwargs)

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