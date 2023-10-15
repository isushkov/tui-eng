from src.helpers.fo import Fo as fo
import re
import pandas as pd
from src.helpers.out import *

class Static:
    def load(name):
        f = f'templates/{name}.txt'
        if name in ['screen','bg']:
            return []
        if not fo.f_exist(f):
            log('static file not exist',f,4)
        lines = fo.txt2list(f, save_spaces=True)
        return [re.sub(r'\{\s*\}', '', line) for line in lines]

    def save_raw(lines, name):
        lines = [re.sub(r'\{\s*\w*\s*\}', '', line) for line in lines]
        fo.list2txt(lines, f'templates/cache/{name}.txt')
        return True

    def load_df(f):
        df = pd.read_csv(f)
        df = df.rename(columns=lambda x: x.strip())
        return df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
