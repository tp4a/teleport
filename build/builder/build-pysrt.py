# -*- coding: utf-8 -*-

import shutil
import struct

from core import colorconsole as cc
from core import makepyo
from core import utils
from core.context import *
from core.env import env

ctx = BuildContext()

MODULES_WIN = ['_asyncio', '_bz2', '_ctypes', '_hashlib', '_lzma', '_overlapped', '_socket', '_sqlite3', '_ssl', 'select', 'sqlite3',
               'libcrypto-1_1', 'libssl-1_1', 'unicodedata']
PY_LIB_REMOVE_WIN = ['ctypes/test', 'curses', 'dbm', 'distutils', 'email/test', 'ensurepip', 'idlelib', 'lib2to3',
                     'lib-dynload', 'pydoc_data', 'site-packages', 'sqlite3/test', 'test', 'tkinter', 'turtledemo',
                     'unittest', 'venv', 'wsgiref', 'doctest.py', 'pdb.py', 'py_compile.py', 'pydoc.py',
                     'this.py', 'wave.py', 'webbrowser.py', 'zipapp.py']
PY_LIB_REMOVE_LINUX = ['ctypes/test', 'curses', 'dbm', 'distutils', 'ensurepip', 'idlelib', 'lib2to3',
                       'lib-dynload', 'pydoc_data', 'site-packages', 'sqlite3/test', 'test', 'tkinter', 'turtledemo', 'unittest', 'venv',
                       'wsgiref', 'doctest.py', 'pdb.py', 'py_compile.py', 'pydoc.py', 'this.py', 'wave.py', 'webbrowser.py', 'zipapp.py']
PY_MODULE_REMOVE_LINUX = ['_ctypes_test', '_testbuffer', '_testcapi', '_testimportmultiple', '_testmultiphase', '_xxtestfuzz']


class PYSBase:
    def __init__(self):
        self.base_path = os.path.join(env.root_path, 'out', 'pysrt', ctx.dist_path)
        self.modules_path = os.path.join(self.base_path, 'modules')

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

        cc.n('upgrade pip ...')
        utils.sys_exec('{} -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip --upgrade'.format(env.py_exec))

        pip = self._get_pip()
        pypi_modules = ['ldap3', 'mako', 'Pillow', 'psutil', 'pymysql', 'qrcode', 'tornado', 'wheezy.captcha']
        for p in pypi_modules:
            cc.n('install {} ...'.format(p))
            utils.sys_exec('{} install -i https://pypi.tuna.tsinghua.edu.cn/simple {}'.format(pip, p), direct_output=True)

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

    def _get_pip(self):
        pass

    def _copy_modules(self):
        cc.n('copy python extension dll...')
        utils.makedirs(self.modules_path)

        ext = utils.extension_suffixes()
        cc.v('extension ext:', ext)
        for m in self.modules:
            for n in ext:
                s = os.path.join(self.py_dll_path, m) + n
                if os.path.exists(s):
                    cc.v('copy %s' % s)
                    cc.v('  -> %s' % os.path.join(self.modules_path, m) + n)
                    shutil.copy(s, os.path.join(self.modules_path, m) + n)

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

        cc.v('compile .py to .pyc...')
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


class PYSWin(PYSBase):
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
        _exec_path = os.path.dirname(env.py_exec)
        # _win_system_path = os.path.join(os.getenv('SystemRoot'), 'system32')
        # if ctx.bits == BITS_32 and ctx.host_os_is_win_x64:
        #     _win_system_path = os.path.join(os.getenv('SystemRoot'), 'SysWOW64')

        if not os.path.exists(_exec_path):
            raise RuntimeError('can not locate python folder at:', _exec_path)

        pydll = self._get_py_dll_name()
        shutil.copy(os.path.join(_exec_path, pydll), os.path.join(self.base_path, pydll))

        if ctx.py_ver == '34':
            msvcrdll = 'msvcr100.dll'
        elif ctx.py_ver == '37':
            msvcrdll = 'vcruntime140.dll'
        else:
            raise RuntimeError('unknown msvc runtime for this python version.')
        shutil.copy(os.path.join(_exec_path, msvcrdll), os.path.join(self.base_path, msvcrdll))

        super()._copy_modules()

    def _get_pip(self):
        _exec_path = os.path.dirname(env.py_exec)
        return os.path.join(_exec_path, 'Scripts', 'pip.exe')

    def _make_py_ver_file(self):
        # 指明python动态库的文件名，这样壳在加载时才知道如何加载python动态库
        out_file = os.path.join(self.base_path, 'python.ver')
        _data = struct.pack('=64s', self._get_py_dll_name().encode())
        f = open(out_file, 'wb')
        f.write(_data)
        f.close()

    def _get_py_dll_name(self):
        return 'python{}.dll'.format(env.py_ver_str)


class PYSLinux(PYSBase):
    def __init__(self):
        super().__init__()

        self.PATH_PYTHON_ROOT = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '..'))
        if not os.path.exists(self.PATH_PYTHON_ROOT):
            raise RuntimeError('can not locate py-static release folder.')

        self.py_lib_remove = PY_LIB_REMOVE_LINUX
        self.py_lib_remove.append('config-{}m-x86_64-linux-gnu'.format(ctx.py_dot_ver))

    def _locate_dll_path(self):
        _path = os.path.join(self.PATH_PYTHON_ROOT, 'lib', 'python{}'.format(ctx.py_dot_ver), 'lib-dynload')
        if os.path.exists(_path):
            return _path

        cc.e('\ncan not locate python DLLs path at [{}]'.format(_path))
        raise RuntimeError()

    def _locate_lib_path(self):
        _path = os.path.join(self.PATH_PYTHON_ROOT, 'lib', 'python{}'.format(ctx.py_dot_ver))
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
        utils.copy_ex(self.py_dll_path, self.modules_path)

        cc.v('remove useless modules...')
        for i in PY_MODULE_REMOVE_LINUX:
            utils.remove(self.modules_path, '{}.cpython-{}m-x86_64-linux-gnu.so'.format(i, ctx.py_ver))

        ext = utils.extension_suffixes()
        files = os.listdir(self.modules_path)
        for i in files:
            for n in ext:
                if i.find('_failed{}'.format(n)) != -1:
                    utils.remove(self.modules_path, i)

    def _get_pip(self):
        _exec_path = os.path.dirname(env.py_exec)
        return os.path.join(_exec_path, 'pip')

    def _make_py_ver_file(self):
        # do nothing.
        pass


def main():
    if not env.init():
        return

    if ctx.host_os == 'windows':
        x = PYSWin()
    elif ctx.host_os == 'linux':
        x = PYSLinux()
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
