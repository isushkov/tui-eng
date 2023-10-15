import sys
import signal
import curses
import inspect
import datetime
import json
import yaml
import pprint
from colorama import Fore, Style
pp = pprint.PrettyPrinter(indent=4)

# exit-handler
def fexit(m='exit:<empty_msg>'):
    curses.endwin() # корректное завершение
    print(m)
    sys.exit(0)
def signal_handler(sig, frame):
    fexit('Ctrl+C. exit.')
signal.signal(signal.SIGINT, signal_handler)

# logging
out = 'main' # +'.log' or 'stdout')
pfx_len_allowed = 35
enable_colors = True

def log(*args):
    # args
    if len(args) == 0: msg, details, status = None,    None,       'info'
    if len(args) == 1: msg, details, status = args[0], None,       'info'
    if len(args) == 2: msg, details, status = args[0], args[1],    'info'
    if len(args)  > 2: msg, details, status = args[0], args[1:-1], args[-1]
    # now
    now = datetime.datetime.now().strftime("%H:%M:%S")
    # log_err_pfx
    stack = inspect.stack()[1]
    func = '' if stack.function == '<module>' else f'{stack.function}()'
    pfx_len = len(now)+5+len(stack.filename)+1+len(str(stack.lineno))+1+len(func)
    if pfx_len > pfx_len_allowed:
        cut_size = pfx_len - pfx_len_allowed + 2 # for '..'
        filepath = '..'+stack.filename[cut_size:]
    elif pfx_len < pfx_len_allowed:
        add_zise = pfx_len_allowed - pfx_len
        filepath = ' '*add_zise + stack.filename
    elif pfx_len == pfx_len_allowed:
        filepath = stack.filename
    log_err_pfx = f'{now} {filepath}:{stack.lineno}:{func}'
    # marker
    need_exit = False
    if   status in [-1, 'verb' ]: color = '';          marker = '[?]'
    elif status in [0,  'info' ]: color = Fore.BLUE;   marker = '[*]'
    elif status in [1,  'ok'   ]: color = Fore.GREEN;  marker = '[+]'
    elif status in [2,  'note' ]: color = Fore.YELLOW; marker = '[!]'
    elif status in [3,  'error']: color = Fore.RED;    marker = '[-]'
    elif status in [4,  'exit' ]: color = Fore.RED;    marker = '[e]'; need_exit = True
    else: fexit(f'{log_err_pfx} Log error: unknown status ({status})')
    # enable/disable colors
    rst = Style.RESET_ALL
    if not enable_colors: color, rst = '', ''
    marker = color + marker + rst
    # path
    path = f'{filepath}:{stack.lineno}:{color}{func}'
    # msg
    msg = '' if (msg is None) or (isinstance(msg, str) and not msg) else ' '+str(msg)
    # details: 1 arg
    if log_is_one_arg(details):
        if isinstance(details, (list, tuple)):
            details = details[0]
        # none
        if details is None: details = rst
        elif isinstance(details, str) and not details: details = rst
        # false
        elif not details: details = f':{rst} "{str(details)}" {type(details)}'
        details = str(details)
        # oneline
        if details == rst: details = rst
        elif '\n' not in details: details = f':{rst} {str(details)}'
        # multiline
        else:
            fin_details = f':\n'
            for i,line in enumerate(details.splitlines()):
                fin_details += f'   {color}|{rst} {line}'
                if i != len(details.splitlines())-1: fin_details += '\n'
            details = fin_details+rst
    # details: 2 or more args
    else:
        fin_details = f':\n'
        for i,detail in enumerate(details):
            fin_details += f'  {color}{i}:{rst} '
            # none/false
            if detail is None or not detail:
                fin_details += f'"{str(detail)}" {type(detail)}'
            # oneline
            elif '\n' not in str(detail):
                fin_details += f'{str(detail)}'
            # multiline
            else:
                for j,line in enumerate(detail.splitlines()):
                    if j == 0: fin_details += line
                    else:      fin_details += f'   {color}:{rst} {line}'
                    if j != len(detail.splitlines())-1: fin_details += '\n'
                fin_details = fin_details+rst
            if i != len(details)-1: fin_details += '\n'
        details = fin_details
    # total
    total = f'{now} {marker} {path}{msg}{details}'
    log_out(total)
    if need_exit: fexit(total)
    return True

def log_is_one_arg(details):
    if isinstance(details, (list, tuple)): return False
    return True

def log_out(msg):
    if out == 'stdout':
        print(msg)
        return True
    with open(f'{out}.log', 'a') as file:
        print(msg, file=file)
    return True
