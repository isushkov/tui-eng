from src.window import Window
from src.static import Static as static
import pandas as pd
from src.helpers.fo import Fo as fo
from src.helpers.out import *
from src.helpers.cmd import Cmd as cmd

class User():
    def __init__(self):
        self.name = self.login()
        self.path = f'data/users/{self.name}'
        self.f_data = f'{self.path}/data.yml'
        self.f_vi = f'{self.path}/vi.csv'
        self.est_matrix = {'F': 0, 'D': 1, 'C': 3, 'B': 6, 'A': 10}
        if fo.f_exist(self.f_data):
            self.data = self.load_user()
        else:
            self.data = self.create_user()
        self.batch_size = self.data['vi_bs']

    def login(self):
        win_screen = Window('screen').refresh()
        win_bg = Window('bg').refresh()
        win = Window('login').refresh()
        # win_man = Window('login_man').refresh()
        name = win.input('login')
        err = False
        if win.menu_is_escape(name):
            err = 'login_err_required'
        else:
            name = name.lower().strip()
            if not name:
                err = 'login_err_required'
            if name == 'default':
                err = 'login_err_reserved'
        if err:
            win = Window(err).refresh()
            win.getch()
            name = self.login()
        return name

    def create_user(self):
        command = f'cp -r data/users/_default {self.path}'
        if not cmd.run(command):
            log('error', command, 4)
        data = fo.yml2dict(self.f_data)
        data['name'] = self.name
        self.save_data(data)
        win = Window('login_ok_created', {'name': self.name}).refresh()
        win.getch()
        return data

    def load_user(self):
        data = fo.yml2dict(self.f_data)
        win = Window('login_ok_loaded', {'name': self.name}).refresh()
        win.getch()
        return data

    def save_data(self, data):
        fo.dict2yml(data, self.f_data, sort=False)
        return True

    def upd_progress_vi(self, batch):
        df = static.load_df(self.f_vi)
        for item in batch:
            prior = item['vi_prior']
            score = item['sc_score']
            estimate = self.get_estimate(score)
            matching_rows = df[df['prior'] == prior]
            if len(matching_rows) > 1:
                log('Prior value not uniq',prior,4)
            if matching_rows.empty:
                tmp = {'prior': [prior], 'score': [score], 'estimate': [estimate]}
                tmp_df = pd.DataFrame(tmp)
                df = pd.concat([df, tmp_df], ignore_index=True)
            else:
                df.loc[df['prior'] == prior, 'score'] = score
                df.loc[df['prior'] == prior, 'estimate'] = estimate
        df.to_csv(self.f_vi, index=False)
        self.save_data(self.data)
        return True
    def get_estimate(self, score):
        for k,v in sorted(self.est_matrix.items(), key=lambda x: -x[1]):
            if score >= v:
                return k

    def upd_statistic(self, f_vi_global):
        sc = static.load_df(self.f_vi)
        vi = static.load_df(f_vi_global)
        self.data['vi_t'] = len(vi)
        for e in ['a', 'b', 'c', 'd', 'f']:
            self.data[f'vi_{e}'] = len(sc[sc['estimate'] == e.upper()])
        self.save_data(self.data)

    def change_batch_size(self):
        while True:
            win = Window('user_bs', {'bs': self.data['vi_bs']}).refresh()
            bs = win.input('bs')
            if win.menu_is_escape(bs):
                break
            bs = bs.lower().strip()
            err = False
            if not bs.isdigit():
                err = 'must be digit.'
            elif int(bs) <= 9 or int(bs) >= 1000:
                err = 'must be "> 9" or "< 1000".'
            if not err:
                self.data['vi_bs'] = int(bs)
                self.save_data(self.data)
                win = Window('user_bs_ok', {'bs': bs}).refresh()
                win.getch()
                break
            win = Window('user_bs_err', {'bs': bs, 'err': err}).refresh()
            ch = win.getch()
            key = chr(ch)
            if key in 'mM':
                return 'main_menu'
            elif key in 'qQ':
                win.menu_bye()
            else:
                self.change_batch_size()
                break
        return 'main_menu'
