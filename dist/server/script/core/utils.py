# -*- coding: utf8 -*-

import os
import platform
import shutil
import subprocess
import sys
import time

from . import colorconsole as cc
from .env import env


def remove(*args):
    path = os.path.join(*args)

    # cc.v(' - remove [%s] ... ' % path, end='')
    if not (os.path.exists(path) or os.path.islink(path)):
        # cc.v('not exists, skip.')
        return

    cc.v(' - remove [%s] ... ' % path, end='')
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


def make_dirs(path, exist_ok=True):
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


def ensure_file_exists(filename):
    if not os.path.exists(filename):
        raise RuntimeError('file not exists: {}'.format(filename))
    if not os.path.isfile(filename):
        raise RuntimeError('path exists but not a file: {}'.format(filename))


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
            # cc.o((cc.CR_GRAY, line), end='\n')
            cc.v(line, end='\n')

        output.append(line)

    ret = p.wait()

    return ret, output


if __name__ == '__main__':
    pass
