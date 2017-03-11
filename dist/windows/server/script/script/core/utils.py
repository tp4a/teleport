# -*- coding: utf8 -*-

import os
import platform
import shutil
import subprocess
import sys
import time

from . import colorconsole as cc
from .env import env

# from .configs import cfg

# try:
#     CONFIG_FILE = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')), 'config.ini')
#     if not cfg.init(CONFIG_FILE):
#         sys.exit(1)
# except:
#     cc.e('can not load configuration.\n\nplease copy `config.ini.in` into `config.ini` and modify it to fit your condition and try again.')
#     sys.exit(1)


# THIS_PATH = os.path.abspath(os.path.dirname(__file__))
# ROOT_PATH = os.path.abspath(os.path.join(THIS_PATH, '..'))


# def _check_download_file(file_name):
#     if env.is_win:
#         # use 7z to test integrity of downloaded
#         ret, output = sys_exec('"{}" t "{}"'.format(env.zip7, file_name), False)
#         if 'Everything is Ok' in output:
#             return True
#     else:
#         cc.e('fixme.')
#         return False
#
#
# def download_file(desc, url, target_path, file_name):
#     cc.n('download {} ... '.format(desc), end='')
#
#     local_file_name = os.path.join(target_path, file_name)
#     if os.path.exists(local_file_name):
#         if not _check_download_file(local_file_name):
#             cc.w('already exists but broken, download it again...')
#         else:
#             cc.w('already exists, skip.')
#             return True
#
#     cc.v('')
#     # 因为下载过程会在命令行显示进度，所以不能使用subprocess.Popen()的方式捕获输出，会很难看！
#     if env.is_win:
#         cmd = '""{}" --no-check-certificate {} -O "{}""'.format(env.wget, url, local_file_name)
#         os.system(cmd)
#     elif env.is_linux:
#         os.system('wget --no-check-certificate {} -O "{}"'.format(url, local_file_name))
#     else:
#         return False
#
#     if not os.path.exists(local_file_name) or not _check_download_file(local_file_name):
#         cc.e('downloading {} from {} failed.'.format(desc, url))
#         return False
#
#     return True
#

# def extension_suffixes():
#     # imp.get_suffixes()
#     # 返回3元组列表(suffix, mode, type), 获得特殊模块的描述
#     #   .suffix为文件后缀名;
#     #   mode为打开文件模式;
#     #   type为文件类型, 1代表PY_SOURCE, 2代表PY_COMPILED, 3代表C_EXTENSION
#
#     EXTENSION_SUFFIXES = list()
#     if cfg.is_py2:
#         suf = imp.get_suffixes()
#         for s in suf:
#             if s[2] == 3:
#                 EXTENSION_SUFFIXES.append(s[0])
#     else:
#         EXTENSION_SUFFIXES = importlib.machinery.EXTENSION_SUFFIXES
#
#     if cfg.dist == 'windows':
#         if '.dll' not in EXTENSION_SUFFIXES:
#             EXTENSION_SUFFIXES.append('.dll')
#
#     elif cfg.dist == 'linux':
#         if '.so' not in EXTENSION_SUFFIXES:
#             EXTENSION_SUFFIXES.append('.so')
#
#     elif cfg.dist == 'macos':
#         raise RuntimeError('not support MacOS now.')
#
#     return EXTENSION_SUFFIXES


def remove(*args):
    path = os.path.join(*args)

    cc.v(' - remove [%s] ... ' % path, end='')
    if not os.path.exists(path):
        cc.v('not exists, skip.')
        return

    for i in range(5):
        cc.v('.', end='')
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
                time.sleep(0.5)
            else:
                os.unlink(path)
        except:
            pass

        if os.path.exists(path):
            time.sleep(1)
        else:
            break

    if os.path.exists(path):
        cc.e('[failed]')
        raise RuntimeError('')
    else:
        cc.i('[done]')


def makedirs(path, exist_ok=True):
    if os.path.exists(path):
        if not exist_ok:
            raise RuntimeError('path already exists: %s' % path)
        else:
            return

    for i in range(5):
        try:
            os.makedirs(path)
        except:
            time.sleep(1)
            pass

        if not os.path.exists(path):
            time.sleep(1)
        else:
            break

    if not os.path.exists(path):
        raise RuntimeError('can not create: %s' % path)


# def copy_file(s_path, t_path, f_name, force=True):
#     if isinstance(f_name, str):
#         f_from = f_name
#         f_to = f_name
#     elif isinstance(f_name, tuple):
#         f_from = f_name[0]
#         f_to = f_name[1]
#     else:
#         raise RuntimeError('utils.copy_file() got invalid param.')
#
#     s = os.path.join(s_path, f_from)
#     t = os.path.join(t_path, f_to)
#     if os.path.exists(t):
#         if force:
#             cc.v('  an exists version found, clean up...')
#             remove(t)
#         else:
#             cc.w('  an exists version found, skip copy.')
#             return
#
#     if not os.path.exists(t_path):
#         makedirs(t_path)
#     cc.v('copy [%s]\n  -> [%s]' % (s, t))
#     shutil.copy(s, t)


def copy_ex(s_path, t_path, item_name=None, force=True):
    if item_name is None:
        s = s_path
        t = t_path
    else:
        if isinstance(item_name, str):
            f_from = item_name
            f_to = item_name
        elif isinstance(item_name, tuple):
            f_from = item_name[0]
            f_to = item_name[1]
        else:
            raise RuntimeError('utils.copy_ex() got invalid param.')

        s = os.path.join(s_path, f_from)
        t = os.path.join(t_path, f_to)

    if os.path.exists(t):
        if force:
            remove(t)
        else:
            cc.w(t, 'already exists, skip copy.')
            return

    if os.path.isdir(s):
        cc.v(' - copy [%s]\n     -> [%s]' % (s, t))
        shutil.copytree(s, t)
    else:
        if not os.path.exists(t_path):
            os.makedirs(t_path)
        cc.v(' - copy [%s]\n     -> [%s]' % (s, t))
        shutil.copy(s, t)


# def update_file(s_path, t_path, f_name):
#     if isinstance(f_name, str):
#         f_from = f_name
#         f_to = f_name
#     elif isinstance(f_name, tuple):
#         f_from = f_name[0]
#         f_to = f_name[1]
#     else:
#         raise RuntimeError('utils.update_file() got invalid param.')
#
#     s = os.path.join(s_path, f_from)
#     t = os.path.join(t_path, f_to)
#     if not os.path.exists(s):
#         cc.w('try update file `%s` but not exists, skip.' % f_from)
#         return
#
#     # TODO: check file MD5 and update time.
#
#     if os.path.exists(t):
#         remove(t)
#
#     if not os.path.exists(t_path):
#         makedirs(t_path)
#     cc.v('update [%s]\n    -> [%s]' % (s, t))
#     shutil.copy(os.path.join(s_path, f_from), t)


def ensure_file_exists(filename):
    if not os.path.exists(filename):
        raise RuntimeError('file not exists: {}'.format(filename))
    if not os.path.isfile(filename):
        raise RuntimeError('path exists but not a file: {}'.format(filename))


# def root_path():
#     return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


# def python_exec():
#     if not os.path.exists(sys.executable):
#         raise RuntimeError('Can not locate Python execute file.')
#     return sys.executable


def sys_exec(cmd, direct_output=False, output_codec=None):
    if output_codec is None:
        if env.is_win:
            output_codec = 'gb2312'
        else:
            output_codec = 'utf8'

    p = None
    if env.is_win:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    else:
        p = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    output = list()
    f = p.stdout
    while True:
        line = f.readline()
        if 0 == len(line):
            break

        line = line.rstrip('\r\n')

        if direct_output:
            cc.o((cc.CR_GRAY, line), end='\n')

        output.append(line)

    ret = p.wait()

    return ret, output


if __name__ == '__main__':
    # test()
    pass
