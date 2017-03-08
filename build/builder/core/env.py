# -*- coding: utf8 -*-

import os
import platform
import sys
import configparser

from . import colorconsole as cc


class Env(object):
    BITS_32 = 32
    BITS_64 = 64

    def __init__(self):
        _this_path = os.path.abspath(os.path.dirname(__file__))

        self.root_path = os.path.abspath(os.path.join(_this_path, '..', '..', '..'))
        self.build_path = os.path.abspath(os.path.join(_this_path, '..', '..'))
        self.builder_path = os.path.join(self.build_path, 'builder')
        self.win32_tools_path = os.path.join(self.build_path, 'tools', 'win32')

        self.is_py2 = sys.version_info[0] == 2
        self.is_py3 = sys.version_info[0] == 3

        self.py_ver = platform.python_version_tuple()
        self.py_ver_str = '%s%s' % (self.py_ver[0], self.py_ver[1])
        self.py_exec = sys.executable

        self.bits = self.BITS_32
        self.bits_str = 'x86'

        _bits = platform.architecture()[0]
        if _bits == '64bit':
            self.bits = self.BITS_64
            self.bits_str = 'x64'

        self.is_win = False
        self.is_win_x64 = False
        self.is_linux = False
        self.is_macos = False

        _os = platform.system().lower()
        self.plat = ''
        if _os == 'windows':
            self.is_win = True
            self.plat = 'windows'
            self.is_win_x64 = 'PROGRAMFILES(X86)' in os.environ
        elif _os == 'linux':
            self.is_linux = True
            self.plat = 'linux'
        elif _os == 'darwin':
            self.is_macos = True
            self.plat = 'macos'

    def init(self):
        if not self._load_config():
            return False

        return True

    def _load_config(self):
        _cfg_file = os.path.join(self.root_path, 'config.ini')
        if not os.path.exists(_cfg_file):
            cc.e('can not load configuration.\n\nplease copy `config.ini.in` into `config.ini` and modify it to fit your condition and try again.')
            return False

        _cfg = configparser.ConfigParser()
        _cfg.read(_cfg_file)
        if 'external_ver' not in _cfg.sections() or 'toolchain' not in _cfg.sections():
            cc.e('invalid configuration file: need `external_ver` and `toolchain` section.')
            return False

        _tmp = _cfg['external_ver']
        try:
            self.ver_openssl = _tmp['openssl']
            self.ver_libuv = _tmp['libuv']
            self.ver_mbedtls = _tmp['mbedtls']
            self.ver_sqlite = _tmp['sqlite']
            self.ver_libssh = _tmp['libssh']
            self.ver_jsoncpp = _tmp['jsoncpp']
            self.ver_mongoose = _tmp['mongoose']
        except IndexError:
            cc.e('invalid configuration file: not all necessary external version are set.')
            return False

        _tmp = _cfg['toolchain']
        if self.is_win:
            if 'wget' in _tmp:
                self.wget = _tmp['wget']
            else:
                self.wget = None
            if self.wget is None or not os.path.exists(self.wget):
                cc.w(' - can not find `wget.exe`, you can get it at https://eternallybored.org/misc/wget/')

            if '7z' in _tmp:
                self.zip7 = _tmp['7z']
            else:
                self.zip7 = None
            if self.zip7 is None or not os.path.exists(self.zip7):
                cc.w(' - can not find `7z.exe`, you can get it at http://www.7-zip.org')

            if 'msbuild' in _tmp:
                self.msbuild = _tmp['msbuild']
            else:
                self.msbuild = self._get_msbuild()

            if self.msbuild is None or not os.path.exists(self.msbuild):
                cc.w(' - can not locate `MSBuild`, so I can build nothing.')

            if 'nsis' in _tmp:
                self.nsis = _tmp['nsis']
            else:
                self.nsis = self._get_nsis()

            if self.nsis is None or not os.path.exists(self.nsis):
                cc.w(' - can not locate `nsis`, so I can not make installer.')

        elif self.is_linux:
            if 'cmake' in _tmp:
                self.cmake = _tmp['cmake']
            else:
                self.cmake = '/usr/bin/cmake'

            if not os.path.exists(self.cmake):
                cc.e(' - can not locate `cmake`, so I can not build binary from source.')
                return False

        return True

    def _get_msbuild(self):
        # 14.0 = VS2015
        # 12.0 = VS2012
        #  4.0 = VS2008
        chk = ['14.0', '4.0', '12.0']

        msp = None
        for c in chk:
            msp = self._winreg_read("SOFTWARE\\Microsoft\\MSBuild\\ToolsVersions\\{}".format(c), 'MSBuildToolsPath')
            if msp is not None:
                break

        if msp is None:
            return None

        return os.path.join(msp[0], 'MSBuild.exe')

    def _get_nsis(self):
        p = self._winreg_read_wow64_32(r'SOFTWARE\NSIS\Unicode', '')
        if p is None:
            return None

        return os.path.join(p[0], 'makensis.exe')

    def _winreg_read(self, path, key):
        try:
            import winreg
            hkey = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ)
            value = winreg.QueryValueEx(hkey, key)
            return value
        except OSError:
            return None

    def _winreg_read_wow64_32(self, path, key):
        try:
            import winreg
            hkey = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
            value = winreg.QueryValueEx(hkey, key)
            return value
        except OSError:
            return None


env = Env()
del Env

if __name__ == '__main__':
    pass
