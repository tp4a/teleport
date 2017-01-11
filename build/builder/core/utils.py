#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import platform
import shutil
import subprocess
import sys
import time

from . import colorconsole as cc

from .configs import cfg
try:
    CONFIG_FILE = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'config.py')
    if not cfg.init(CONFIG_FILE):
        sys.exit(1)
except:
    cc.e('can not load configuration.\n\nplease copy `config.py.in` into `config.py` and modify it to fit your condition and try again.')
    sys.exit(1)

# PY_VER = platform.python_version_tuple()
#IS_PY2 = sys.version_info[0] == 2
#IS_PY3 = sys.version_info[0] == 3

if cfg.is_py2:
    import imp
elif cfg.is_py3:
    import importlib
    import importlib.machinery

    if sys.platform == 'win32':
        import winreg


def extension_suffixes():
    # imp.get_suffixes()
    # 返回3元组列表(suffix, mode, type), 获得特殊模块的描述
    #   .suffix为文件后缀名;
    #   mode为打开文件模式;
    #   type为文件类型, 1代表PY_SOURCE, 2代表PY_COMPILED, 3代表C_EXTENSION

    EXTENSION_SUFFIXES = list()
    if cfg.is_py2:
        suf = imp.get_suffixes()
        for s in suf:
            if s[2] == 3:
                EXTENSION_SUFFIXES.append(s[0])
    else:
        EXTENSION_SUFFIXES = importlib.machinery.EXTENSION_SUFFIXES

    if cfg.dist == 'windows':
        if '.dll' not in EXTENSION_SUFFIXES:
            EXTENSION_SUFFIXES.append('.dll')

    elif cfg.dist == 'linux':
        if '.so' not in EXTENSION_SUFFIXES:
            EXTENSION_SUFFIXES.append('.so')

    elif cfg.dist == 'macos':
        raise RuntimeError('not support MacOS now.')

    # cc.v(EXTENSION_SUFFIXES)
    return EXTENSION_SUFFIXES


def remove(*args):
    path = os.path.join(*args)

    cc.v('remove [%s] ...' % path, end='')
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
        cc.e('failed')
        raise RuntimeError('')
    else:
        cc.i('done')


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


def copy_file(s_path, t_path, f_name, force=True):
    if isinstance(f_name, str):
        f_from = f_name
        f_to = f_name
    elif isinstance(f_name, tuple):
        f_from = f_name[0]
        f_to = f_name[1]
    else:
        raise RuntimeError('utils.copy_file() got invalid param.')

    s = os.path.join(s_path, f_from)
    t = os.path.join(t_path, f_to)
    if os.path.exists(t):
        if force:
            cc.v('  an exists version found, clean up...')
            remove(t)
        else:
            cc.w('  an exists version found, skip copy.')
            return

    if not os.path.exists(t_path):
        makedirs(t_path)
    cc.v('copy [%s]\n  -> [%s]' % (s, t))
    shutil.copy(s, t)


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
        cc.v('copy [%s]\n  -> [%s]' % (s, t))
        shutil.copytree(s, t)
    else:
        if not os.path.exists(t_path):
            os.makedirs(t_path)
        cc.v('copy [%s]\n  -> [%s]' % (s, t))
        shutil.copy(s, t)


def update_file(s_path, t_path, f_name):
    if isinstance(f_name, str):
        f_from = f_name
        f_to = f_name
    elif isinstance(f_name, tuple):
        f_from = f_name[0]
        f_to = f_name[1]
    else:
        raise RuntimeError('utils.update_file() got invalid param.')

    s = os.path.join(s_path, f_from)
    t = os.path.join(t_path, f_to)
    if not os.path.exists(s):
        cc.w('try update file `%s` but not exists, skip.' % f_from)
        return

    # TODO: check file MD5 and update time.

    if os.path.exists(t):
        remove(t)

    if not os.path.exists(t_path):
        makedirs(t_path)
    cc.v('update [%s]\n    -> [%s]' % (s, t))
    shutil.copy(os.path.join(s_path, f_from), t)


def ensure_file_exists(filename):
    if not os.path.exists(filename):
        raise RuntimeError('file not exists: {}'.format(filename))
    if not os.path.isfile(filename):
        raise RuntimeError('path exists but not a file: {}'.format(filename))


# def root_path():
#     return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def python_exec():
    if not os.path.exists(sys.executable):
        raise RuntimeError('Can not locate Python execute file.')
    return sys.executable


g_msbuild_path = None


def msbuild_path():
    global g_msbuild_path
    if g_msbuild_path is not None:
        return g_msbuild_path

    # 14.0 = VS2015
    # 12.0 = VS2012
    #  4.0 = VS2008
    chk = ['14.0', '4.0', '12.0']

    msp = None
    for c in chk:
        msp = winreg_read("SOFTWARE\\Microsoft\\MSBuild\\ToolsVersions\\{}".format(c), 'MSBuildToolsPath')
        if msp is not None:
            break

    if msp is None:
        raise RuntimeError('Can not locate MSBuild.')

    msb = os.path.join(msp[0], 'MSBuild.exe')
    if not os.path.exists(msb):
        raise RuntimeError('Can not locate MSBuild at {}'.format(msp))

    g_msbuild_path = msb
    return msb


g_nsis_path = None


def nsis_path():
    global g_nsis_path
    if g_nsis_path is not None:
        return g_nsis_path

    if 'nsis' in cfg:
        g_nsis_path = cfg['nsis']
        return g_nsis_path

    p = winreg_read_wow64_32(r'SOFTWARE\NSIS\Unicode', '')
    if p is None:
        raise RuntimeError('Can not locate unicode version of NSIS.')

    p = os.path.join(p[0], 'makensis.exe')
    if not os.path.exists(p):
        raise RuntimeError('Can not locate NSIS at {}'.format(p))

    g_nsis_path = p
    return p


def winreg_read(path, key):
    try:
        hkey = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ)
        value = winreg.QueryValueEx(hkey, key)
    except OSError:
        return None

    return value


def winreg_read_wow64_32(path, key):
    try:
        hkey = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
        value = winreg.QueryValueEx(hkey, key)
    except OSError:
        return None

    return value


def sys_exec(cmd, direct_output=False, output_codec=None):
    # 注意：output_codec在windows默认为gb2312，其他平台默认utf8
    _os = platform.system().lower()
    if output_codec is None:
        if _os == 'windows':
            output_codec = 'gb2312'
        else:
            output_codec = 'utf8'

    p = None
    if _os == 'windows':
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    else:
        p = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    output = ''
    f = p.stdout
    while True:
        line = f.readline()
        if 0 == len(line):
            break

        if direct_output:
            # cc.v(line.decode(output_codec))
            cc.v(line, end='')

        output += line

    ret = p.wait()

    return (ret, output)


def msvc_build(sln_file, proj_name, target, platform, force_rebuild):
    msbuild = msbuild_path()

    if force_rebuild:
        cmd = '"{}" "{}" "/target:clean" "/property:Configuration={};Platform={}"'.format(msbuild, sln_file, target, platform)
        ret, _ = sys_exec(cmd, direct_output=True)
        cc.v('ret:', ret)

    cmd = '"{}" "{}" "/target:{}" "/property:Configuration={};Platform={}"'.format(msbuild, sln_file, proj_name, target, platform)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('build MSVC project `{}` failed.'.format(proj_name))


def nsis_build(nsi_file, _define=''):
    nsis = nsis_path()
    cmd = '"{}" /V2 {} /X"SetCompressor /SOLID /FINAL lzma" "{}"'.format(nsis, _define, nsi_file)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('make installer with nsis failed. [{}]'.format(nsi_file))


def cmake(work_path, target, force_rebuild, cmake_define=''):
    # because cmake v2.8 shipped with Ubuntu 14.04LTS, but we need 3.5.
    # so we copy a v3.5 cmake from CLion and put to $WORK/eomsoft/toolchain/cmake.
    #CMAKE = os.path.abspath(os.path.join(root_path(), 'toolchain', 'cmake', 'bin', 'cmake'))
    if 'cmake' not in cfg:
        raise RuntimeError('please set `cmake` path.')
    if not os.path.exists(cfg['cmake']):
        raise RuntimeError('`cmake` does not exists, please check your config.py and try again.')

    CMAKE = cfg['cmake']

    cc.n('make by cmake', target, sep=': ')
    old_p = os.getcwd()
    # new_p = os.path.dirname(wscript_file)

    # work_path = os.path.join(root_path(), 'cmake-build')
    if os.path.exists(work_path):
        if force_rebuild:
            remove(work_path)
    if not os.path.exists(work_path):
        makedirs(work_path)

    os.chdir(work_path)
    if target == 'debug':
        target = 'Debug'
    else:
        target = 'Release'
    cmd = '"{}" -DCMAKE_BUILD_TYPE={} {} ..;make'.format(CMAKE, target, cmake_define)
    ret, _ = sys_exec(cmd, direct_output=True)
    os.chdir(old_p)
    if ret != 0:
        raise RuntimeError('build with cmake failed, ret={}. [{}]'.format(ret, target))


def strip(filename):
    cc.n('strip binary file', filename)
    if not os.path.exists(filename):
        return False
    cmd = 'strip {}'.format(filename)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('failed to strip binary file [{}], ret={}.'.format(filename, ret))
    return True


def make_zip(src_path, to_file):
    cc.v('compress folder into .zip...')
    n, _ = os.path.splitext(to_file)
    # x = os.path.split(to_file)[1].split('.')
    p = os.path.dirname(to_file)
    shutil.make_archive(os.path.join(p, n), 'zip', src_path)
    ensure_file_exists(to_file)


def make_targz(work_path, folder, to_file):
    cc.v('compress folder into .tar.gz...')
    old_p = os.getcwd()

    os.chdir(work_path)
    cmd = 'tar zcf "{}" "{}"'.format(to_file, folder)
    ret, _ = sys_exec(cmd, direct_output=True)
    ensure_file_exists(to_file)
    os.chdir(old_p)


def fix_extension_files(s_path, t_path):
    cc.n('\nfix extension files...')
    # 遍历s_path目录下的所有Python扩展文件（动态库），并将其移动到t_path目录下，同时改名。
    # 例如， s_path/abc/def.pyd -> t_path/abc.def.pyd

    s_path = os.path.abspath(s_path)
    t_path = os.path.abspath(t_path)

    ext = extension_suffixes()
    s_path_len = len(s_path)

    def _fix_(s_path, t_path, sub_path):
        for parent, dir_list, file_list in os.walk(sub_path):
            for d in dir_list:
                _fix_(s_path, t_path, os.path.join(parent, d))

            for filename in file_list:
                _, e = os.path.splitext(filename)
                if e in ext:
                    f_from = os.path.join(parent, filename)
                    f_to = f_from[s_path_len + 1:]
                    f_to = f_to.replace('\\', '.')
                    f_to = f_to.replace('/', '.')
                    f_to = os.path.join(t_path, f_to)

                    cc.v('move: ', f_from, '\n   -> ', f_to)
                    shutil.move(f_from, f_to)

    _fix_(s_path, t_path, s_path)


if __name__ == '__main__':
    # test()
    pass
