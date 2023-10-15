import curses
import random
import re
import time
import string
from src.ui import Ui
from src.template import Template
from src.static import Static as static
from src.helpers.fo import Fo as fo
from src.helpers.out import *


class Window:
    ui = None
    tmpl = None

    def __init__(self, name, data4context=False, stdscr=False, render=True):
        if Window.ui   is None: Window.ui   = Ui(curses, stdscr)
        if Window.tmpl is None: Window.tmpl = Template(self.ui)
        log(f'>> start {name}')
        self.name = name
        self.data = self.tmpl.get_win_data(self.name, data4context)
        self.h = self.data['hw'][0]
        self.w = self.data['hw'][1]
        self.y = self.data['yx'][0]
        self.x = self.data['yx'][1]
        self.win = self.ui.scr.subwin(*self.data['hw'], *self.data['yx'])
        if render:
            self.render()

    # render
    def render(self):
        self.render_fill()
        self.render_static()
        self.render_context()
        self.render_border()
        self.render_title()
        return self
    def render_fill(self):
        chars = self.data['fill']['chars']
        color = self.data['fill']['color']
        self.color('on', color)
        for y in range(self.h - 1):
            for x in range(self.w - 1):
                self.win.addch(y, x, self.choose_char(chars))
        self.color('off', color)
        return True
    def render_static(self):
        border_offset = 1 if self.data['border'] else 0
        y,x = border_offset, border_offset+self.data['w_padding']
        lines = static.load(self.name)
        for i,line in enumerate(lines):
            self.render_static_line(y+i,x, line, 'c')
        static.save_raw(lines, self.name)
        return True
    def render_static_line(self, y,x, line, color):
        match = re.search(r'\{([rygbdc])\}', line)
        if not match:
            self.insstr(y,x, line, color)
            return True
        before = line[:match.start()]
        if before:
            self.insstr(y,x, before, color)
            x += len(before)
        color = match.group(1)
        after = line[match.end():]
        self.render_static_line(y,x, after, color)
        return True
    def render_context(self):
        for k,v in self.data['context'].items():
            self.render_context_item(v)
    def render_context_item(self, context):
        val = context.get('val')
        if val is None:
            return False
        align = context['align']
        chars = context['chars']
        color = context['color']
        mode  = context['mode']
        cl    = context['cl']
        w     = context['w']
        text = self.tmpl.fill_text(val, w, align, chars)
        y,x = self.tmpl.cl2yx(self.data, cl)
        if mode == 'ins':
            self.insstr(y,x, text, color)
        else:
            self.addstr(y,x, text, color)
        return True
    def render_border(self):
        if not self.data['border']:
            return False
        color = self.data['border']['color']
        self.color('on', color)
        self.win.border()
        self.color('off', color)
        return True
    def render_title(self):
        title = self.data['title']
        if not title:
            return False
        val = str(title['val'])
        chars = title['chars']
        align = title['align']
        color = title['color']
        text = self.tmpl.fill_text(val, title['w'], 'c', chars)
        x,_  = self.tmpl.align_offsets(val, align, self.w)
        self.addstr(0,x, text, color)
        return True

    # helpers.self
    def refresh(self):
        self.win.refresh()
        return self
    def addstr(self, y,x, text, color='c'):
        self.win.addstr(y,x, text, self.ui.cm[color])
        return self
    def addch(self, y,x, text, color='c'):
        self.win.addch(y,x, text, self.ui.cm[color])
        return self
    def insstr(self, y,x, text, color='c'):
        self.win.insstr(y,x, text, self.ui.cm[color])
        return self
    def insch(self, y,x, text, color='c'):
        self.win.insch(y,x, text, self.ui.cm[color])
        return self
    def sleep(self, sec):
        time.sleep(sec)
        return self
    def cursor(self, status):
        if status not in ['on','off']:
            log('wrong param (must be on/off)',status,4)
        if status == 'on':  self.ui.crs.curs_set(True)
        if status == 'off': self.ui.crs.curs_set(False)
        return True
    def move(self, y,x):
        self.ui.scr.move(self.y+y,self.x+x)
        return self
    def color(self, mode, color):
        if mode == 'on':  self.win.attron(self.ui.cm[color])
        if mode == 'off': self.win.attroff(self.ui.cm[color])
        return self
    # helpers.other
    def getch(self):
        ch = self.ui.scr.getch()
        return ch
    def getkey(self):
        key = self.ui.scr.getkey()
        return key
    def get_wch(self):
        wch = self.ui.scr.get_wch()
        return wch
    def ungetch(self, ch):
        self.ui.crs.ungetch(ch)
    def unget_wch(self, wch):
        self.ui.crs.unget_wch(wch)
    def choose_char(self, chars):
        return random.choice(chars) if len(chars) > 1 else chars

    # menu
    def menu_bye(self):
        Window('menu_bye').refresh().sleep(0.5)
        fexit('Bye.')
    def menu_is_escape(self, inp):
        return True if inp is False else False
    def menu_unknown(self, ch):
        if   ch == 9:   symbol = 'Tab'
        elif ch == 10:  symbol = 'Enter'
        elif ch == 27:  symbol = 'Escape'
        elif ch == 263: symbol = 'Backspace'
        elif ch == 330: symbol = 'Delete'
        else:
            self.ungetch(ch)
            symbol = self.get_wch()
        win = Window('menu_unknown', {'key': symbol}).refresh()
        win.getch()

    # input
    def input(self, input_name):
        context = self.data['inputs'][input_name]
        max_len = context['max_len']
        chars   = context['chars']
        color_t = context['color_t']
        color_p = context['color_p']
        y,x     = self.tmpl.cl2yx(self.data, context['cl'])
        default_txt = ''.join(self.choose_char(chars) for i in range(max_len+1))
        self.ui.crs.flushinp()
        self.addstr(y,x, default_txt, color_p).refresh()
        self.move(y,x)
        self.cursor('on')
        inp = ''
        while True:
            self.addstr(y,x, inp, color_t).refresh()
            ch = self.getch()
            if ch in [9,10]: # tab, enter
                break
            elif ch == 27: # escape
                inp = False
                break
            elif ch == 263: # backspace
                inp = inp[:-1]
                self.addstr(y,x+len(inp), self.choose_char(chars), color_p)
            elif ch == 330: # delete
                continue
            # elif left right
            #     fexit('input DEL - left right..')
            elif len(inp) < max_len:
                self.ungetch(ch)
                wch = self.get_wch()
                inp += wch
        self.cursor('off')
        return inp

    # animate
    def addstr_animate_linear(self, y,x, text, delay, color_search='d', color_result='c', search_count=3):
        for i,char in enumerate(text):
            for i in range(search_count):
                self.render_random_char(y,x, color_search, delay)
            self.addstr(y,x, char, color_result).refresh()
            x += 1
        return self

    def addstr_animate_cover(self, y,x, text, delay, color_search='y', color_result='c', search_count=3):
        done_chars = 0
        matrix = {i:0 for i in range(len(text))}
        while done_chars < len(text):
            random_index = random.randint(0, len(text)-1)
            if matrix[random_index] < search_count:
                self.render_random_char(y,x+random_index, color_search, delay)
                matrix[random_index] += 1
            elif matrix[random_index] == search_count:
                self.addstr(y,x+random_index, text[random_index], color_result).refresh()
                matrix[random_index] += 1
                done_chars += 1
        return self

    def render_random_char(self, y,x, color, delay):
        random_char = self.choose_char(string.ascii_letters + string.digits)
        self.addstr(y,x, random_char, color).refresh()
        time.sleep(delay)
        return self
