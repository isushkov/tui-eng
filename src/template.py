import re
from src.helpers.fo import Fo as fo
from src.helpers.out import *
from src.static import Static as static

class Template:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    def __del__(self):
        Template.__instance = None

    def __init__(self, ui):
        self.ui = ui
        self.path = 'templates/_map.yml'
        self.data = fo.yml2dict(self.path)
        self.data_dflt = self.data['_defaults']
        self.ancors = ['tl','tc','tr','ml','mc','mr','bl','bc','br']
        self.win_names = self.get_win_names()

    def get_win_names(self):
        return [k for k in self.data.keys() if not (k.startswith('x_') or k.startswith('_'))]

    def get_win_data(self, win_name, data4context):
        win_data = self.data[win_name]
        win_data = self.parse_key(win_data, 'hw', (list, tuple))
        for k in ['w_padding','extend_hw']:
            win_data = self.parse_key(win_data, k, int)
        for k in ['fill','border','title','context','inputs']:
            win_data = self.parse_key(win_data, k, dict)
        for k in win_data:
            if k not in self.data_dflt:
                log('unknown key',f'.{win_name}.{k}',4)
        if data4context:
            win_data['context'] = self.merge_data_with_context(data4context, win_data['context'])
        win_data = self.extend_hw(win_name, win_data)
        win_data = self.yx(win_name, win_data)
        return win_data

    def merge_data_with_context(self, data, context):
        for k,v in context.items():
            if k in data:
                context[k]['val'] = data[k]
        return context

    def parse_key(self, win_data, k, expected):
        # default
        dflt_param = self.data_dflt[k]
        if k not in win_data:
            win_data[k] = {} if k in ['context', 'inputs'] else dflt_param
        win_param = win_data[k]
        # validate
        if not isinstance(win_param, expected) and win_param is not None:
            log(f'unexpected type .{k}: "{win_param}" {type(win_param)}', \
                f'expected {expected}', 4)
        # disable
        elif not win_param:
            if isinstance(win_param, (list, tuple, set)): win_param = []
            elif isinstance(win_param, dict): win_param = {}
            else: win_param = 0
        # enable.other
        elif isinstance(win_param, bool):
            win_param = int(win_param)
        elif isinstance(win_param, (list, tuple, set)):
            win_param = list(win_param)
        # enable.dict
        elif isinstance(win_param, dict):
            if k not in ['context','inputs']:
                self.dict_valid(win_param, dflt_param, k)
                win_param = self.dict_fill(win_param, dflt_param)
            else:
                for p in win_param:
                    self.dict_valid(win_param[p], dflt_param, p, k)
                    win_param[p] = self.dict_fill(win_param[p], dflt_param)
        win_data[k] = win_param
        return win_data
    def dict_valid(self, dst, src, p, pp=''):
        for k in dst:
            if k not in src and k != 'val':
                log('unknown key', f'{"." if pp else ""}.{p}.{k}', 4)
    def dict_fill(self, dst, src):
        for k in src:
            if k not in dst:
                dst[k] = src[k]
        return dst

    def yx(self, win_name, win_data):
        c_hw = win_data['hw']
        # bg
        if win_name == 'screen':
            win_data['hw'] = self.ui.crs.LINES, self.ui.crs.COLS
            win_data['yx'] = [0,0]
            return win_data
        if win_name == 'bg':
            p = { 'hw': [self.ui.crs.LINES, self.ui.crs.COLS], 'yx': [0,0] }
            win_data['yx'] = self.layout('mc', p, c_hw, [0,0], is_bg=True)
            return win_data
        # default
        if 'yx' not in win_data:
            win_data['yx'] = self.data_dflt['yx']
        # absolute
        if isinstance(win_data['yx'], (list, tuple)):
            return self.parse_key(win_data, 'yx', (list, tuple))
        # layout.parse
        m = re.match(r'^(\w+\(?\w+\)?)([+-]\d+)([+-]\d+)$', win_data['yx'])
        if m: layout, y_ofs, x_ofs = m.group(1), int(m.group(2)), int(m.group(3))
        else: layout, y_ofs, x_ofs = win_data['yx'], 0, 0
        i = layout.find('(')
        j = layout.find(')')
        if i != -1 and j != -1:
            ancor  = layout[:i]
            parent = layout[i+1:j]
        else:
            ancor = layout
            parent = 'bg'
        if ancor not in self.ancors or parent not in self.win_names:
            log(f'wrong layout name', f'.{win_name}.yx: {win_data["yx"]}',4)
        # layout.apply
        p = self.data[parent]
        o_hw = y_ofs, x_ofs
        win_data['yx'] = self.layout(ancor, p,c_hw,o_hw)
        return win_data

    def layout(self, ancor, p,c_hw,o_hw, is_bg=False):
        if ancor == 'mc':
            y = ((p['hw'][0] - c_hw[0]) // 3) + o_hw[0]
            x = ((p['hw'][1] - c_hw[1]) // 2) + o_hw[1]
            y,x = self.layout_bg_ofs(y,x, is_bg)
        elif ancor == 'tl':
            y = p['yx'][0] + o_hw[0]
            x = p['yx'][1] + o_hw[1]
        elif ancor == 'br':
            y = p['hw'][0] - c_hw[0] + o_hw[0] - 1
            x = p['hw'][1] - c_hw[1] + o_hw[1] - 1
            y,x = self.layout_bg_ofs(y,x, is_bg)
        else:
            log(f'todo: layout format', layout, 4)
        return y,x
    def layout_bg_ofs(self, y,x, is_bg):
        if is_bg:
            return y,x
        b_yx = self.data['bg']['yx']
        return y + b_yx[0], x + b_yx[1]

    def extend_hw(self, win_name, win_data):
        if not win_data['extend_hw']:
            return win_data
        h = win_data['hw'][0]
        w = win_data['hw'][1]
        border_offset = 2 if win_data['border'] else 0
        max_len = 0
        # by title
        title = win_data.get('title')
        if title:
            text = title['val']
            len_title = len(text)
            l,r = self.align_offsets(text, 'c', title['w'])
            len_line = l + len_title + r
            if len_line > max_len:
                max_len = len_line
        # by static
        lines = static.load(win_name)
        context = win_data['context']
        for i,line in enumerate(lines):
            len_line = len(re.sub(r'\{\s*\w*\s*\}', '', line))
            # by context
            len_line = self.extend_hw_by_context(win_data, len_line, context)
            if len_line > max_len:
                max_len = len_line
        h_extend = border_offset + len(lines)
        w_extend = border_offset + win_data['w_padding']*2 + max_len
        h = h_extend if h_extend > h else h
        w = w_extend if w_extend > w else w
        win_data['hw'] = h,w
        return win_data
    def extend_hw_by_context(self, win_data, len_line, context):
        for k,v in context.items():
            if v['mode'] not in ['ins', 'cov']:
                log('invalid template - mode:', mode, 4)
            len_val = len(str(v['val']))
            if v['mode'] == 'ins':
                len_line += len_val
                continue
            x_ofs = self.cl2yx(win_data, v['cl'])[1]
            if x_ofs + len_val > len_line:
                len_line = x_ofs + len_val
        return len_line

    # helpers.cl2yx
    def cl2yx(self, win_data, cl):
        border_offset = 1 if win_data['border'] else 0
        y = cl[0] + border_offset - 1
        x = cl[1] + border_offset + win_data['w_padding'] - 1
        return y,x

    # helpers.align
    def fill_text(self, text, w, align, chars):
        l,r = self.align_offsets(text, align, w)
        text = self.align_fill(text, chars, l,r)
        return text
    def align_offsets(self, text, align, len_line):
        text = str(text)
        if isinstance(len_line, str):
            if not re.match(r'^a\d+$', len_line):
                log('invalid template',f'.context.<context_name>.w: "{len_line}"',4)
            len_line = len(text) + int(len_line[1:])
        if len_line < len(text):
            return 0,0
        if align == 'c':
            len_left = (len_line - len(text)) // 2
        else:
            if   len(align) == 1: offset = 0
            elif len(align)  > 1: offset = int(align[1:])
            if   align[0] == 'l': len_left = int(offset)
            elif align[0] == 'r': len_left = len_line - offset - len(text)
        len_right = len_line - len(text) - len_left
        return len_left, len_right
    def align_fill(self, text, chars, len_left, len_right):
        left  = self.align_fill_side(chars, len_left)
        right = self.align_fill_side(chars, len_right)
        return left + str(text) + right
    def align_fill_side(self, chars, length):
        if len(chars) > 1:
            line = ''
            for i in range(length):
                line += random.choice(chars)
            return line
        return chars*length
