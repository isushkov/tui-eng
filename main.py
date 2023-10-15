import curses
import re
from src.ui import Ui
from src.window import Window
from src.user import User
from src.verbs_irregular import VerbsIrregular
from src.helpers.out import *
from src.template import Template

log('\n\n\n')
log('>>> run >>>>>>>>>>>>>>>>>>>>')

def main(stdscr):
    win_screen = Window('screen', stdscr=stdscr).refresh()
    win_bg = Window('bg').refresh()
    # login
    user = User()
    # main_menu
    while True:
        win = Window('main_menu', user.data).refresh()
        ch = win.getch()
        key = chr(ch)
        if key in 'vV':
            vi = VerbsIrregular(user)
            res = vi.run()
            if res != 'main_menu':
                break
        elif key in 'qQ': win.menu_bye()
        else:
            win.menu_unknown(ch)
    # exit
    log('Exit. End of script.','',4)

if __name__ == '__main__':
    curses.wrapper(main)
