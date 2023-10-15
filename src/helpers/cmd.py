import os
import subprocess
import time
import re
from src.helpers.fo import Fo as fo
from src.helpers.out import *

class Cmd:
    # exec bash cmd inside python:
    #   cmd:          комманда
    #   strict:       если команда завершилась ошибкой прекратить выполнение python скрипта
    #   verbose:      показывать команду/return_code/stdout/stderr
    #   verbose4ok:   показывать команду/return_code/stdout/stderr если ошибки небыло
    #   verbose4fail: показывать команду/return_code/stdout/stderr если была ошибка
    @classmethod
    def run(cls, cmd, strict=True, verbose4fail=True, verbose4ok=False, verbose=False):
        # validate params
        cmd = cmd.strip()
        if cmd == 'pwd':
            return {'code': 0, 'success': True, 'out': os.getcwd(), 'err': False}
        if cmd.split(' ', 1)[0] == 'cd':
            return os.chdir(cmd.split(' ', 1)[1])
        # run cmd
        reply = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, encoding='utf-8')
        # post-processing
        out = reply.stdout.strip()
        err = reply.stderr.strip()
        if reply.returncode == 0:
            success = True
            if verbose or verbose4ok:
                cls.verbose_print(success, cmd, reply.returncode, err, out)
        if reply.returncode != 0 or err:
            success = False
            if verbose or verbose4fail:
                cls.verbose_print(success, cmd, reply.returncode, err, out)
            if strict:
                exit()
        return {'code': reply.returncode, 'success': success, 'out': out, 'err': err}

    @staticmethod
    def verbose_print(success, cmd, code, err, out):
        status = 'ok' if success else 'error'
        log('Run cmd', cmd, status)
        log('Return cmd [code]', '   '+str(code), status)
        log('Return cmd [std_err]', err, status)
        log('Return cmd [std_out]', out, status)

    # @classmethod
    # def ssh(cls, user, host, cmd, strict=True):
    #     ssh_args=f'-o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout={cls.co["global"]["ssh"]["timeout"]}'
    #     result = cls.run(f'ssh {user}@{host} {ssh_args} {cmd}', strict=strict)
    #     if result['code'] == 0:
    #         log('success', f'{user}@{host}: {cmd}')
    #     else:
    #         log('failed', f'{user}@{host}: {cmd}', 3)
    #     return result

    @classmethod
    def check_ssh(cls, host, user):
        if cls.ssh(user, host, cmd='echo ok', strict=False)['code'] != 0:
            log('failed', host, 3)
            return False
        return True

    @classmethod
    def check_sudo(cls, host, user):
        if cls.ssh(user, host, cmd='sudo echo ok', strict=False)['code'] != 0:
            log('failed', host, 3)
            return False
        return True

    def scp(src, dst, send_pass=False):
        print(dst.split(':', 1))
        host, f = dst.split(':', 1)
        print(host)
        print(f)
        exit()
        # TODO: check if is dir
        arg_r = '-r' if is_dir else ''
        pfx = f'sshpass -p {ssh_pass}' if send_pass else ''
        ssh_pfx = f'{pfx} ssh {ssh_user}@{dst}'
        scp_pfx = f'{pfx} scp {arg_r} {ssh_user}@{dst}'
        before_script = 'src/collector/nginx/scp_before.sh'
        commands = [
            f"if [ -d {target_dir} ]; then rm -r {target_dir}; fi",
            f"if [ -f {target_dir} ]; then rm {target_dir}; fi",
            f"mkdir -p {target_dir}",
            f"{ssh_pfx} 'bash -s' < {before_script} {ssh_user} {source_dir}",
            f"{scp_pfx}:/home/{ssh_user}/wofr_tmp {target_dir}",
            f"{ssh_pfx} 'rm -r /home/{ssh_user}/wofr_tmp'"
        ]
        for cmd in commands:
            self.run(cmd, strict=True, verbose4fail=True)

    def cp_remote(host, src, dst, send_pass=False):
        asdf
        return False

    # short
    @classmethod
    def pwd(cls): return cls.run('pwd')['out']
    # file
    @classmethod
    def ln(cls, d):
        return cls.run(f'mkdir -p {d}')
    # dir
    @classmethod
    def mkdir(cls, d): return cls.run(f'mkdir -p {d}')
    @classmethod
    def cd(cls, d): return cls.run(f'cd {d}')
    @classmethod
    def rm(cls, path): return cls.run(f'rm -rf {path}')
    @classmethod
    def dirfiles(cls, d):
        return cls.run(f'find {d} -maxdepth 1 -type f')['out'].split('\n')

    # massive
    @classmethod
    def save(cls, data, f, sort=False, aliases=True, frm='yml'):
        cls.run(f'mkdir -p {fo.dirname(f)}')
        if frm == 'yml':
            fo.dict2yml(data, f, sort, aliases)
        if frm == 'json':
            fo.dict2json(data, f)
        log('file', f)
        return True
    @staticmethod
    def load(f, show_not_exist=True):
        if not fo.f_exist(f):
            if show_not_exist: log('file not found', f, 3)
            return False
        data = fo.yml2dict(f)
        if not data:
            log('broken data', f, 3)
            return False
        log('file', f)
        return data
    @classmethod
    def backup(cls, d_src):
        if not re.match('^data/', d_src):
            log('uncorrect data path', d_src, 3)
            exit()
        if not fo.d_exist(d_src):
            log('data dir not found', d_src, 2)
            return False
        kind = re.match("^data/(.*)$", d_src).group(1)
        t = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        d_dst = f'backups/{kind}/{t}'
        cls.run(f'cp -r {d_src} {d_dst}')
        start_pwd = cls.pwd()
        cls.cd(f'backups/{kind}')
        cls.run('rm -f last')
        cls.run(f'ln -s {t} last')
        cls.cd(start_pwd)
        log('created', d_dst, 1)
        return True
