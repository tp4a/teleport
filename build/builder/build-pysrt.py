# -*- coding: utf-8 -*-

import shutil
import struct

import sys

from core import colorconsole as cc
from core import makepyo
from core import utils
from core.context import *
from core.env import env


ctx = BuildContext()

MODULES_WIN = ['_bz2', '_ctypes', '_hashlib', '_lzma', '_overlapped', '_socket', '_sqlite3', '_ssl', 'select', 'sqlite3', 'unicodedata']
PY_LIB_REMOVE_WIN = ['ctypes/test', 'curses', 'dbm', 'distutils', 'email/test', 'ensurepip', 'idlelib', 'lib2to3',
                     'lib-dynload', 'pydoc_data', 'site-packages', 'sqlite3/test', 'test', 'tkinter', 'turtledemo',
                     'unittest', 'venv', 'wsgiref', 'dis.py', 'doctest.py', 'pdb.py', 'py_compile.py', 'pydoc.py',
                     'this.py', 'wave.py', 'webbrowser.py', 'zipapp.py']
PY_LIB_REMOVE_LINUX = ['ctypes/test', 'curses', 'config-3.4m-x86_64-linux-gnu', 'dbm', 'distutils', 'ensurepip', 'idlelib', 'lib2to3',
                       'lib-dynload', 'pydoc_data', 'site-packages', 'sqlite3/test', 'test', 'tkinter', 'turtledemo', 'unittest', 'venv',
                       'wsgiref', 'dis.py', 'doctest.py', 'pdb.py', 'py_compile.py', 'pydoc_data', 'pydoc.py', 'this.py', 'wave.py',
                       'webbrowser.py', 'zipapp.py']


class PYSBase:
    def __init__(self):
        self.base_path = os.path.join(env.root_path, 'out', 'pysrt', ctx.dist_path)

        self.py_dll_path = ''
        self.py_lib_path = ''

        self.modules = list()
        self.py_lib_remove = list()
        self.PY_STATIC_PATH = ''

    def build(self):
        self.py_dll_path = self._locate_dll_path()
        self.py_lib_path = self._locate_lib_path()

        cc.v('python dll path     :', self.py_dll_path)
        cc.v('python lib path     :', self.py_lib_path)

        self._make_base()
        self._make_python_zip()
        self._make_py_ver_file()

    def _locate_dev_inc_path(self):
        return ''

    def _locate_dll_path(self):
        return ''

    def _locate_lib_path(self):
        return ''

    def _make_base(self):
        pass

    def _copy_modules(self):
        cc.n('copy python extension dll...')
        mod_path = os.path.join(self.base_path, 'modules')
        utils.makedirs(mod_path)

        ext = utils.extension_suffixes()
        cc.v('extension ext:', ext)
        for m in self.modules:
            for n in ext:
                s = os.path.join(self.py_dll_path, m) + n
                if os.path.exists(s):
                    cc.v('copy %s' % s)
                    cc.v('  -> %s' % os.path.join(mod_path, m) + n)
                    shutil.copy(s, os.path.join(mod_path, m) + n)

    def _make_python_zip(self):
        cc.n('make python.zip...')

        out_file = os.path.join(self.base_path, 'python.zip')
        if os.path.exists(out_file):
            utils.remove(out_file)

        _tmp_ = os.path.join(self.base_path, '_tmp_')
        if os.path.exists(_tmp_):
            cc.v('clear up temp folder...')
            utils.remove(_tmp_)

        cc.v('copying Python `Lib` folder...')
        shutil.copytree(self.py_lib_path, _tmp_)

        cc.v('remove useless folders and files...')
        for i in self.py_lib_remove:
            utils.remove(_tmp_, i)

        cc.v('generate *.pyo...')
        makepyo.make(_tmp_)

        cc.v('compress into python.zip...')
        utils.make_zip(_tmp_, out_file, from_parent=False)
        utils.ensure_file_exists(out_file)

        cc.v('remove temp folder...')
        utils.remove(_tmp_)

    def _make_py_ver_file(self):
        pass

    def _get_py_dll_name(self):
        return ''


class PYSBaseWin(PYSBase):
    def __init__(self):
        super().__init__()
        self.modules = MODULES_WIN
        self.py_lib_remove = PY_LIB_REMOVE_WIN

    def _locate_dev_inc_path(self):
        for p in sys.path:
            if os.path.exists(os.path.join(p, 'include', 'pyctype.h')):
                return os.path.join(p, 'include')
        cc.e('\ncan not locate python development include path in:')
        for p in sys.path:
            cc.e('  ', p)
        raise RuntimeError()

    def _locate_dll_path(self):
        for p in sys.path:
            if os.path.exists(os.path.join(p, 'DLLs', '_ctypes.pyd')):
                return os.path.join(p, 'DLLs')
        cc.e('\nCan not locate python DLLs path in:')
        for p in sys.path:
            cc.e('  ', p)
        raise RuntimeError()

    def _locate_lib_path(self):
        for p in sys.path:
            if os.path.exists(os.path.join(p, 'Lib', 'ctypes', 'wintypes.py')):
                return os.path.join(p, 'Lib')
        cc.e('\nCan not locate python lib path in:')
        for p in sys.path:
            cc.e('  ', p)
        raise RuntimeError()

    def _make_base(self):
        if os.path.exists(self.base_path):
            cc.v('an exists version found, clean up...', self.base_path)
            utils.remove(self.base_path)

        cc.v('make pysbase folder...')
        utils.makedirs(self.base_path)

        cc.v('copy python core dll...')
        _win_system_path = os.path.join(os.getenv('SystemRoot'), 'system32')
        if ctx.bits == BITS_32 and ctx.host_os_is_win_x64:
            _win_system_path = os.path.join(os.getenv('SystemRoot'), 'SysWOW64')

        if not os.path.exists(_win_system_path):
            raise RuntimeError('can not locate windows system folder at:', _win_system_path)

        pydll = self._get_py_dll_name()
        shutil.copy(os.path.join(_win_system_path, pydll), os.path.join(self.base_path, pydll))

        if ctx.py_ver == '34':
            msvcrdll = 'msvcr100.dll'
        else:
            raise RuntimeError('unknown msvc runtime for this python version.')
        shutil.copy(os.path.join(_win_system_path, msvcrdll), os.path.join(self.base_path, msvcrdll))

        super()._copy_modules()

    def _make_py_ver_file(self):
        # 在python.zip尾部追加一个字符串（补零到64字节），指明python动态库的文件名，这样壳在加载时才知道如何加载python动态库
        out_file = os.path.join(self.base_path, 'python.ver')
        _data = struct.pack('=64s', self._get_py_dll_name().encode())
        f = open(out_file, 'wb')
        f.write(_data)
        f.close()

    def _get_py_dll_name(self):
        #return 'python{}{}.dll'.format(PY_VER[0], PY_VER[1])
        return 'python{}.dll'.format(utils.cfg.py_ver_str)


class PYSBaseLinux(PYSBase):
    def __init__(self):
        super().__init__()

        self.PY_STATIC_PATH = os.path.join(os.path.join(env.root_path, 'external', 'linux', 'release'))
        if not os.path.exists(self.PY_STATIC_PATH):
            raise RuntimeError('can not locate py-static release folder.')

        self.py_lib_remove = PY_LIB_REMOVE_LINUX

    def _locate_dll_path(self):
        _path = os.path.join(self.PY_STATIC_PATH, 'lib', 'python3.4', 'lib-dynload')
        if os.path.exists(_path):
            return _path

        cc.e('\ncan not locate python DLLs path at [{}]'.format(_path))
        raise RuntimeError()

    def _locate_lib_path(self):
        _path = os.path.join(self.PY_STATIC_PATH, 'lib', 'python3.4')
        if os.path.exists(os.path.join(_path, 'ctypes', 'wintypes.py')):
            return _path

        cc.e('\ncan not locate python lib path at [{}]'.format(_path))
        raise RuntimeError()

    def _make_base(self):
        if os.path.exists(self.base_path):
            cc.v('an exists version found, clean up...', self.base_path)
            utils.remove(self.base_path)

        cc.v('make pysrt folder...')
        utils.makedirs(self.base_path)

        cc.n('copy python extension dll...')
        utils.copy_ex(self.py_dll_path, os.path.join(self.base_path, 'modules'))

    def _make_py_ver_file(self):
        # do nothing.
        pass


def main():
    if not env.init():
        return

    if ctx.host_os == 'windows':
        x = PYSBaseWin()
    elif ctx.host_os == 'linux':
        x = PYSBaseLinux()
    else:
        raise RuntimeError('unsupported platform:', ctx.host_os)

    x.build()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        cc.e(e.__str__())
    except:
        cc.f('got exception.')
