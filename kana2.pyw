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
NTRIES = 4

JAP_FONT = ['MS Gothic', 'notosanscjkjp']
LATIN_FONT = ['Arial Narrow', 'Arial']
TITLE_FONT = 'Verdana'

class Mode(enum.Enum):
    KANA_TO_LATIN = 1
    LATIN_TO_KANA = 2
    KANA_TO_LATIN_TEXT = 3

class Charset(enum.Flag):
    HIRAGANA = 1
    KATAKANA = 2
    EXT = 4

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

HIRAGANA_ALL_CHARS = HIRAGANA_CHARS + HIRAGANA_EXT_CHARS

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

KATAKANA_ALL_CHARS = KATAKANA_CHARS + KATAKANA_EXT_CHARS

ALL_CHARS = HIRAGANA_ALL_CHARS + KATAKANA_ALL_CHARS

#endregion

CHARSETS = {
    Charset.HIRAGANA: HIRAGANA_CHARS,
    Charset.KATAKANA: KATAKANA_CHARS,
    Charset.HIRAGANA | Charset.KATAKANA: HIRAGANA_CHARS + KATAKANA_CHARS,
    Charset.HIRAGANA | Charset.EXT: HIRAGANA_ALL_CHARS,
    Charset.KATAKANA | Charset.EXT: KATAKANA_ALL_CHARS,
    Charset.HIRAGANA | Charset.KATAKANA | Charset.EXT: ALL_CHARS,
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

    def event(self, event: pg.event.Event) -> bool | None:
        if event.type == pg.MOUSEBUTTONDOWN:
            return self.mouse_down(event)
        elif event.type == pg.MOUSEBUTTONUP:
            return self.mouse_up(event)
        elif event.type == pg.MOUSEMOTION:
            return self.mouse_move(event)
        elif event.type == pg.KEYDOWN:
            return self.key_down(event)
        elif event.type == pg.KEYUP:
            return self.key_up(event)

    def mouse_down(self, event: pg.event.Event) -> bool | None:
        pass

    def mouse_up(self, event: pg.event.Event) -> bool | None:
        pass

    def mouse_move(self, event: pg.event.Event) -> bool | None:
        pass

    def key_down(self, event: pg.event.Event) -> bool | None:
        pass

    def key_up(self, event: pg.event.Event) -> bool | None:
        pass


class Label(Widget):
    def __init__(self, text: str, rect, font=None, *, text_color=(0, 0, 0),
                 bg_color=None, border_width=0, border_radius=0,
                 border_color=(0, 0, 0), hover_color=None, click_color=None,
                 select_color=None, disabled_color=None, align='center',
                 selected=False, visible=True, enabled=True, data=None,
                 on_click=None):
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
        assert align in {'center', 'left', 'right'}
        self.align = align
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
            return True

    def mouse_up(self, event):
        if self.enabled and self.clicking and self.rect.collidepoint(event.pos):
            if self.on_click:
                self.on_click(self)
        self.clicking = False

    def mouse_move(self, event):
        self.hovering = self.rect.collidepoint(event.pos)

    def toggle_selected(self):
        self.selected = not self.selected

    def get_bg_color(self):
        return (self.disabled_color if not self.enabled and self.disabled_color
                else self.click_color if self.clicking and self.click_color
                else self.hover_color if self.hovering and self.hover_color
                else self.select_color if self.selected and self.select_color
                else self.bg_color)

    def get_text_color(self):
        return self.text_color

    def get_text(self):
        return self.text

    def text_rect(self):
        size = self.font.size(self.get_text())
        if self.align == 'center':
            return crect(self.rect.center, size)
        elif self.align == 'left':
            return mkrect(size, midleft=self.rect.midleft)
        elif self.align == 'right':
            return mkrect(size, midright=self.rect.midright)
        else:
            raise ValueError(self.align)

    def draw(self, screen):
        if not self.visible:
            return
        bg_color = self.get_bg_color()
        if bg_color:
            pg.draw.rect(screen, bg_color, self.rect, 0,
                         self.border_radius)
        text_img = self.font.render(
            self.get_text(), True, self.get_text_color())
        screen.blit(text_img, self.text_rect())
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
        self.cursor = 0

    def clear(self):
        self.text = ''
        self.cursor = 0

    def key_down(self, event):
        if not self.enabled:
            return False
        if event.key == pg.K_RETURN:
            if self.on_enter:
                self.on_enter(self)
        elif event.key == pg.K_BACKSPACE:
            if self.cursor > 0:
                self.text = self.text[:self.cursor-1] + self.text[self.cursor:]
                self.cursor -= 1
        elif event.key == pg.K_DELETE:
            self.text = self.text[:self.cursor] + self.text[self.cursor+1:]
        elif event.key == pg.K_LEFT:
            self.cursor = max(self.cursor - 1, 0)
        elif event.key == pg.K_RIGHT:
            self.cursor = min(self.cursor + 1, len(self.text))
        elif event.key == pg.K_HOME:
            self.cursor = 0
        elif event.key == pg.K_END:
            self.cursor = len(self.text)
        elif event.unicode and event.unicode.isprintable():
            self.text = (self.text[:self.cursor] + event.unicode +
                         self.text[self.cursor:])
            self.cursor += len(event.unicode)
        else:
            return False
        return True

    def draw(self, screen):
        super().draw(screen)
        if pg.time.get_ticks() % 1000 < 500:
            bar_img = self.font.render('|', True, self.get_text_color())
            rect = self.text_rect()
            xpos = rect.left + self.font.size(self.text[:self.cursor])[0]
            bar_rect = bar_img.get_rect(y=rect.y, centerx=xpos)
            screen.blit(bar_img, bar_rect)


class Scene(Widget):
    def __init__(self, game: 'Game'):
        self.game = game
        self.widgets: list[Widget] = []
        self.bg_color = BGCOLOR

    def event(self, event: pg.event.Event):
        for w in self.widgets:
            if w.event(event):
                return True
        return super().event(event)

    def add(self, widget: Widget):
        self.widgets.append(widget)
        return widget

    def add_all(self, *widgets: Widget):
        for widget in widgets:
            self.widgets.append(widget)
        return widgets

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
        self.mode: Mode = Mode.KANA_TO_LATIN
        self.charset: Charset = Charset.HIRAGANA
        self.init_ui()

    def init_ui(self):
        # main_label = Label('Kana/仮名', (WIDTH//2, HEIGHT//2-110),
        main_label = Label('Ｋａｎａ／仮名', (WIDTH//2, HEIGHT//2-110),
                           SysFont(JAP_FONT, 60))
        bstyle = {
            'font': SysFont(LATIN_FONT, 24),
            'bg_color': (192, 192, 255),
            'select_color': (0, 192, 255),
            'hover_color': (64, 128, 255),
        }
        mode_button1 = Button(
            'Kana→Latin', crect((WIDTH//2 - 150, HEIGHT//2 - 15), (130, 50)),
            on_click=self.handle_mode, data=Mode.KANA_TO_LATIN, selected=True,
            **bstyle)
        mode_button2 = Button(
            'Latin→Kana', crect((WIDTH//2, HEIGHT//2 - 15), (130, 50)),
            on_click=self.handle_mode, data=Mode.LATIN_TO_KANA, **bstyle)
        mode_button3 = Button(
            'Kana→Text', crect((WIDTH//2 + 150, HEIGHT//2 - 15), (130, 50)),
            on_click=self.handle_mode, data=Mode.KANA_TO_LATIN_TEXT, **bstyle)
        self.mode_buttons = [mode_button1, mode_button2, mode_button3]

        charset_button1 = Button(
            'Hiragana', crect((WIDTH//2 - 150, HEIGHT//2 + 55), (130, 50)),
            on_click=self.handle_charset, data=Charset.HIRAGANA, selected=True,
            **bstyle)
        charset_button2 = Button(
            'Katakana', crect((WIDTH//2, HEIGHT//2 + 55), (130, 50)),
            on_click=self.handle_charset, data=Charset.KATAKANA, **bstyle)
        charset_button3 = Button(
            '+ Dakuten', crect((WIDTH//2 + 150, HEIGHT//2 + 55), (130, 50)),
            on_click=self.handle_charset, data=Charset.EXT, **bstyle)
        self.charset_buttons = [charset_button1, charset_button2, charset_button3]

        start_button = Button(
            'Start', crect((WIDTH//2, HEIGHT//2 + 150), (150, 80)),
            SysFont(TITLE_FONT, 50), bg_color=(0, 255, 255),
            hover_color=(64, 128, 255), on_click=self.handle_start)

        self.mode_lbl = Label('', (20, 40), align='left', visible=False)
        self.charset_lbl = Label('', (20, 80), align='left', visible=False)

        self.add_all(
            main_label, *self.mode_buttons, *self.charset_buttons,
            self.mode_lbl, self.charset_lbl, start_button,
        )

    def handle_mode(self, button: Button):
        self.mode = button.data
        for button2 in self.mode_buttons:
            button2.selected = button2 is button

    def handle_charset(self, button: Button):
        if (self.charset ^ button.data) & ~Charset.EXT:
            self.charset ^= button.data
            button.toggle_selected()

    def handle_start(self, button):
        self.game.change_scene(GameScene, self.charset, self.mode)

    def update(self):
        self.mode_lbl.text = self.mode.name
        self.charset_lbl.text = self.charset.name

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

        self.add_all(
            self.char_lbl, *answer_widgets, self.wrong_lbl,
            self.score_lbl, self.successes_lbl, self.failures_lbl
        )

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
        if not textbox.text:
            return
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
            self.handle_right(button)
        else:
            self.handle_wrong(button)

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
        if self.mode != Mode.KANA_TO_LATIN_TEXT:
            num_keys = range(pg.K_1, pg.K_1 + NCHOICES)
            if event.key in num_keys:
                ind = num_keys.index(event.key)
                self.handle_choice(self.choice_buttons[ind])
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
        self.running = False
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
