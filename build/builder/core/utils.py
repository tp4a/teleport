# -*- coding: utf8 -*-

import os
import shutil
import subprocess
import sys
import time

from . import colorconsole as cc
from .env import env

if env.is_py2:
    import imp
elif env.is_py3:
    import importlib
    import importlib.machinery


def _check_download_file(file_name):
    if env.is_win:
        # use 7z to test integrity of downloaded
        ret, output = sys_exec('"{}" t "{}"'.format(env.zip7, file_name), False)
        if 'Everything is Ok' in output:
            return True
    else:
        x = os.path.splitext(file_name)
        # print('ext:', x)
        if x[-1].lower() == '.zip':
            ret, output = sys_exec('zip -T "{}"'.format(file_name), False)
            # print('test .zip:', ret, output)
            if ret == 0:
                return True
        elif x[-1].lower() == '.xz':
            ret, output = sys_exec('xz -t "{}"'.format(file_name), False)
            # print('test .xz:', ret, output)
            if ret == 0:
                return True
        elif x[-1].lower() == '.gz':
            ret, output = sys_exec('gzip -t "{}"'.format(file_name), False)
            # print('test .gz:', ret, output)
            if ret == 0:
                return True
        else:
            cc.w('[fixme] how to test {} on Linux? '.format(x[-1]), end='')
            return True

    return False


def download_file(desc, url, target_path, file_name):
    cc.n('download {} ... '.format(desc), end='')

    _temp_file = os.path.join(target_path, '_dl_{}'.format(file_name))
    _real_file = os.path.join(target_path, file_name)

    if os.path.exists(_temp_file):
        cc.w('already exists but broken, download it again...')
        remove(_temp_file)
        remove(_real_file)

        # if not _check_download_file(local_file_name):
        #     cc.w('already exists but broken, download it again...')
        # else:
        #     cc.w('already exists, skip.')
        #     return True

    if os.path.exists(_real_file):
        cc.w('already exists, skip.')
        return True

    cc.v('')
    # 因为下载过程会在命令行显示进度，所以不能使用subprocess.Popen()的方式捕获输出，会很难看！
    if env.is_win:
        cmd = '""{}" --no-check-certificate {} -O "{}""'.format(env.wget, url, _temp_file)
        os.system(cmd)
    elif env.is_linux or env.is_macos:
        os.system('wget --no-check-certificate {} -O "{}"'.format(url, _temp_file))
    else:
        cc.e('can not download, no download tool.')
        return False

    if not os.path.exists(_temp_file) or not _check_download_file(_temp_file):
        cc.e('downloading {} from {} failed.'.format(desc, url))
        return False

    os.rename(_temp_file, _real_file)

    return True


def extension_suffixes():
    # imp.get_suffixes()
    # 返回3元组列表(suffix, mode, type), 获得特殊模块的描述
    #   .suffix为文件后缀名;
    #   mode为打开文件模式;
    #   type为文件类型, 1代表PY_SOURCE, 2代表PY_COMPILED, 3代表C_EXTENSION

    EXTENSION_SUFFIXES = list()
    if env.is_py2:
        suf = imp.get_suffixes()
        for s in suf:
            if s[2] == 3:
                EXTENSION_SUFFIXES.append(s[0])
    else:
        EXTENSION_SUFFIXES = importlib.machinery.EXTENSION_SUFFIXES

    if env.is_win:
        if '.dll' not in EXTENSION_SUFFIXES:
            EXTENSION_SUFFIXES.append('.dll')

    elif env.is_linux:
        if '.so' not in EXTENSION_SUFFIXES:
            EXTENSION_SUFFIXES.append('.so')

    else:
        raise RuntimeError('not support this platform now.')

    return EXTENSION_SUFFIXES


def remove(*args):
    path = os.path.abspath(os.path.join(*args))

    cc.v('remove [%s] ...' % path, end='')
    if not os.path.exists(path):
        cc.v('not exists, skip.')
        return

    for i in range(5):
        cc.v('.', end='')
        try:
            if os.path.isdir(path):
                if path == '/':
                    raise RuntimeError('### What are you doing?!! ###')
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


def sys_exec(cmd, direct_output=False, output_codec=None):
    print(cmd)
    if output_codec is None:
        if env.is_win:
            output_codec = 'gb2312'
        else:
            output_codec = 'utf8'

    p = None
    if env.is_win:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    else:
        p = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True, shell=True)

    output = list()
    f = p.stdout
    while True:
        line = f.readline()
        if 0 == len(line):
            break

        line = line.rstrip('\r\n')

        if direct_output:
            cc.o((cc.CR_CYAN, line), end='\n')

        output.append(line)

    ret = p.wait()

    return (ret, output)


def msvc_build(sln_file, proj_name, target, platform, force_rebuild):
    if env.msbuild is None:
        raise RuntimeError('where is `msbuild`?')

    if force_rebuild:
        cmd = '"{}" "{}" "/target:clean" "/property:Configuration={};Platform={}"'.format(env.msbuild, sln_file, target,
                                                                                          platform)
        ret, _ = sys_exec(cmd, direct_output=True)
        cc.v('ret:', ret)

    cmd = '"{}" "{}" "/target:{}" "/property:Configuration={};Platform={}"'.format(env.msbuild, sln_file, proj_name,
                                                                                   target, platform)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('build MSVC project `{}` failed.'.format(proj_name))


def xcode_build(proj_file, proj_name, target, force_rebuild):
    if force_rebuild:
        cmd = 'xcodebuild -project "{}" -target {} -configuration {} clean'.format(proj_file, proj_name, target)
        ret, _ = sys_exec(cmd, direct_output=True)
        cc.v('ret:', ret)

    cmd = 'xcodebuild -project "{}" -target {} -configuration {}'.format(proj_file, proj_name, target)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('build XCode project `{}` failed.'.format(proj_name))


def make_dmg(json_file, dmg_file):
    out_path = os.path.dirname(dmg_file)
    cc.v(out_path)

    if not os.path.exists(out_path):
        makedirs(out_path)

    cmd = 'appdmg "{}" "{}"'.format(json_file, dmg_file)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('make dmg failed.')


def nsis_build(nsi_file, _define=''):
    if env.nsis is None:
        raise RuntimeError('where is `nsis`?')

    cmd = '"{}" /V2 {} /X"SetCompressor /SOLID /FINAL lzma" "{}"'.format(env.nsis, _define, nsi_file)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('make installer with nsis failed. [{}]'.format(nsi_file))


def cmake(work_path, target, force_rebuild, cmake_define='', cmake_pre_define=''):
    # I use cmake v3.5 which shipped with CLion.
    if env.cmake is None:
        raise RuntimeError('where is `cmake`?')

    cc.n('make by cmake', target, sep=': ')
    old_p = os.getcwd()

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
    cmd = '{} "{}" -DCMAKE_BUILD_TYPE={} {} ..;make'.format(cmake_pre_define, env.cmake, target, cmake_define)
    cc.o(cmd)
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


def fix_new_line_flag(filename):
    cc.n('fix new line flag to CR for text file', filename)
    if not os.path.exists(filename):
        return False
    cmd = 'dos2unix {}'.format(filename)
    ret, _ = sys_exec(cmd, direct_output=True)
    if ret != 0:
        raise RuntimeError('failed to dos2unix file [{}], ret={}.'.format(filename, ret))
    return True


def make_zip(src_path, to_file, from_parent=True):
    cc.v('compress folder into .zip...')

    src_path = os.path.abspath(src_path)
    _parent = os.path.abspath(os.path.join(src_path, '..'))
    _folder = src_path[len(_parent) + 1:]

    if env.is_win:
        old_p = os.getcwd()
        if from_parent:
            os.chdir(_parent)
            cmd = '""{}" a "{}" "{}""'.format(env.zip7, to_file, _folder)
        else:
            os.chdir(src_path)
            cmd = '""{}" a "{}" "*""'.format(env.zip7, to_file)
        os.system(cmd)
        os.chdir(old_p)
    elif env.is_linux:
        old_p = os.getcwd()
        if from_parent:
            os.chdir(_parent)
            cmd = 'zip -r "{}" "{}"'.format(to_file, _folder)
        else:
            os.chdir(src_path)
            cmd = 'zip -q -r "{}" ./*'.format(to_file)
        os.system(cmd)
        os.chdir(old_p)
    else:
        raise RuntimeError('not support this platform.')

    ensure_file_exists(to_file)


def unzip(file_name, to_path):
    if env.is_win:
        cmd = '""{}" x "{}" -o"{}""'.format(env.zip7, file_name, to_path)
        os.system(cmd)
    elif env.is_linux:
        os.system('unzip "{}" -d "{}"'.format(file_name, to_path))
    else:
        raise RuntimeError('not support this platform.')


def make_targz(work_path, folder, to_file):
    cc.v('compress folder into .tar.gz...')
    old_p = os.getcwd()

    os.chdir(work_path)
    cmd = 'tar zcf "{}" "{}"'.format(to_file, folder)
    ret, _ = sys_exec(cmd, direct_output=True)
    ensure_file_exists(to_file)
    os.chdir(old_p)


if __name__ == '__main__':
    # test()
    pass
