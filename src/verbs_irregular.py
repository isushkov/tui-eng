import pandas as pd
import curses
from src.helpers.fo import Fo as fo
from src.helpers.cmd import Cmd as cmd
from src.helpers.out import *
from src.window import Window
from src.static import Static as static

class VerbsIrregular:
    def __init__(self, user):
        self.user = user
        self.f = 'data/verbs_irregular.csv'
        self.est_nexts  = {'F': 1, 'D': 3, 'C': 6, 'B': 10, 'A': 0}

    def menu(self):
        res = False
        while not res:
            win = Window('vi_menu_continue').refresh()
            ch = win.getch()
            key = chr(ch)
            if   key in 'yY': res = 'continue'
            elif key in 'cC': res = 'batch_size'
            elif key in 'mM': res = 'main_menu'
            elif key in 'qQ': win.menu_bye()
            else:
                win.menu_unknown(ch)
                res = self.menu()
        return res

    def run(self):
        # get all batch
        batch = self.get_batch()
        for i,q_data in enumerate(batch):
            # vi
            win = Window('vi').render().refresh()
            win = self.vi_prepare_context(win, i,q_data)
            win.render().refresh()
            # v2
            v2 = self.vx_get_answer('v2')
            if v2 is False: return 'main_menu'
            # v3
            v3 = self.vx_get_answer('v3')
            if v2 is False: return 'main_menu'
            # res
            v2_ok, v3_ok = q_data['vi_v2'], q_data['vi_v3']
            s = self.res_is_success(v2,v2_ok, v3,v3_ok)
            batch[i] = self.res_upd_score(q_data, s)
            win = self.res_prepare_context(win, q_data)
            # render.res
            win = self.res_render(win, s, v2,v2_ok, v3,v3_ok)
            # reset context
            for k in win.data['context']:
                win.data['context'][k]['val'] = None
            # render.resmini
            win_mini = self.resmini_render(s)
            win.getch()
        # batch posthook
        self.user.upd_progress_vi(batch)
        self.user.upd_statistic(self.f)
        Window('vi', self.user.data).refresh()
        res = self.menu()
        if res == 'continue':
            return self.run()
        elif res == 'batch_size':
            return self.user.change_batch_size()
        elif res == 'main_menu':
            return 'main_menu'
        else:
            log('unknown menu res',res,4)
    # vi
    def vi_prepare_context(self, win, i,q_data):
        context = win.data['context']
        context = win.tmpl.merge_data_with_context(self.user.data, context)
        context['vi_batch']['val']    = f'{str(i+1)}/{self.user.data["vi_bs"]}'
        context['sc_prior']['val']    = q_data['sc_prior']
        context['sc_estimate']['val'] = q_data['sc_estimate']
        context['sc_score']['val']    = q_data['sc_score']
        context['sc_estnxt']['val']   = self.est_nexts[q_data['sc_estimate']]
        context['vi_v1']['val']       = q_data['vi_v1']
        context['vi_v1_ipa']['val']   = q_data['vi_v1_ipa']
        return win
    # v2/v3
    def vx_get_answer(self, vx):
        # input
        win = Window(f'vi_{vx}').refresh()
        inp = win.input(vx)
        if win.menu_is_escape(inp):
            return False
        inp = inp.lower().strip()
        # render back
        y,x = win.tmpl.cl2yx(win.data, win.data['inputs'][vx]['cl'])
        Window(f'vi_{vx}_back').addstr(y,x, inp, 'c').refresh()
        return inp
    # res
    def res_is_success(self, v2,v2_ok, v3,v3_ok):
        s = {
            'v2': False,
            'v3': False,
            'total': False
        }
        if v2 == v2_ok: s['v2'] = True
        if v3 == v3_ok: s['v3'] = True
        if s['v2'] and s['v3']: s['total'] = True
        return s
    def res_upd_score(self, q_data, s):
        score = q_data['sc_score']
        if s['total']:
            score += 1
        else:
            score -= 3
            if score < 0:
                score = 0
        q_data['sc_score'] = score
        return q_data
    def res_prepare_context(self, win, q_data):
        win.data['context'] = win.tmpl.merge_data_with_context(q_data, win.data['context'])
        return win
    def res_render(self, win, s, v2,v2_ok, v3,v3_ok):
        delay = 0.02
        cs = 'y'
        # v1,v1_ipa/v2,v2_ipa
        for vx_name in ['v2', 'v3']:
            # v1/v2
            context = win.data['context'][f'vi_{vx_name}']
            y,x = win.tmpl.cl2yx(win.data, context['cl'])
            w = context['w']
            cr = 'g' if s[vx_name] else 'r'
            if s[vx_name]:
                text = context['val']
                win.addstr_animate_linear(y,x, text, delay, cs, cr)
            else:
                vx    = v2    if vx_name == 'v2' else v3
                vx_ok = v2_ok if vx_name == 'v2' else v3_ok
                text_success = self.res_get_vx_success_part(vx, vx_ok)
                text_wrong = self.res_get_vx_wrong_part(vx_ok, text_success)
                text_patch = ''.join(win.choose_char(context['chars']) for _ in range(w-len(vx_ok)))
                success_color = 'r' if text_success == vx_ok else 'g'
                win.addstr_animate_linear(y,x, text_success, delay, cs, success_color)
                win.addstr_animate_linear(y,x+len(text_success), text_wrong, delay, cs, cr)
                win.addstr(y,x+len(vx_ok), text_patch, context['color'])
            # v1_ipa/v2_ipa
            context = win.data['context'][f'vi_{vx_name}_ipa']
            y,x = win.tmpl.cl2yx(win.data, context['cl'])
            w = context['w']
            text = context['val']
            text_empty = ''.join(win.choose_char(context['chars']) for _ in range(w-len(text)))
            cr = 'g' if s[vx_name] else 'r'
            win.addstr_animate_linear(y,x, text, delay, cs, cr)
            win.addstr_animate_linear(y,x+len(text), text_empty, delay, cs, cr, 1)
        # v1_trans
        cr = 'g' if s['total'] else 'r'
        context = win.data['context']['vi_v1_trans']
        y,x = win.tmpl.cl2yx(win.data, context['cl'])
        text = win.tmpl.fill_text(context['val'], context['w'], context['align'], context['chars'])
        win.addstr_animate_cover(y,x, text, delay, cs, cr)
        # v1_example/v2_example/v3_example
        for vx_name in ['v1', 'v2', 'v3']:
            if vx_name == 'v1': cr = 'c'
            else:               cr = 'g' if s[vx_name] else 'r'
            context = win.data['context'][f'vi_{vx_name}_example']
            y,x = win.tmpl.cl2yx(win.data, context['cl'])
            w = context['w']
            chars = context['chars']
            text = context['val']
            text_empty = ''.join(win.choose_char(context['chars']) for _ in range(w-len(text)))
            win.addstr_animate_linear(y,x, text, delay, cs, cr)
            win.addstr_animate_linear(y,x+len(text), text_empty, delay, cs, cr, 1)
        return win
    def res_get_vx_success_part(self, vx, vx_ok):
        match = ''
        for i in range(min(len(vx),len(vx_ok))):
            if vx[i] != vx_ok[i]:
                break
            match += vx[i]
        return match
    def res_get_vx_wrong_part(self, vx_ok, success_part):
        return vx_ok.replace(success_part, '', 1)
    # resmini
    def resmini_render(self, s):
        return Window('vi_res_ok' if s['total'] else 'vi_res_err').refresh()

    # batch
    def get_batch(self):
        vi = static.load_df(self.f)
        sc = static.load_df(self.user.f_vi)
        batch = []
        bs = self.user.batch_size
        if len(batch) < bs: batch = self.get_batch_F(bs, batch, vi, sc)
        if len(batch) < bs: batch = self.get_batch_D(bs, batch, vi, sc)
        if len(batch) < bs: batch = self.get_batch_C(bs, batch, vi, sc)
        if len(batch) < bs: batch = self.get_batch_B(bs, batch, vi, sc)
        if len(batch) < bs: batch = self.get_batch_A(bs, batch, vi, sc)
        if len(batch) < bs: batch = self.get_batch_min_score(bs, batch, vi, sc)
        return batch
    def get_batch_F(self, batch_size, batch, vi, sc):
        for index, row in vi.iterrows():
            # build question
            vi_data = {'vi_'+vi:v for vi,v in row.to_dict().items()}
            sc_data = {'sc_prior': row['prior'],
                       'sc_score': 0,
                       'sc_estimate': 'F'}
            batch_item = {**sc_data, **vi_data}
            # Проверяем, существует ли значение "prior" в sc
            prior = row['prior']
            if prior not in sc['prior'].values:
                batch.append(batch_item)
            else:
                # Если "prior" существует, проверяем значение "score"
                sc_row = sc[sc['prior'] == prior]
                if sc_row['score'].values[0] == 0:
                    batch.append(batch_item)
            # Проверяем размер batch
            if len(batch) >= batch_size:
                break
        return batch
    def get_batch_D(self, batch_size, batch, vi, sc): fexit('find_D')
    def get_batch_C(self, batch_size, batch, vi, sc): fexit('find_C')
    def get_batch_B(self, batch_size, batch, vi, sc): fexit('find_B')
    def get_batch_A(self, batch_size, batch, vi, sc): fexit('find_A')
    def get_batch_min_score(self, batch_size, batch, vi, sc): fexit('find_min_score')
