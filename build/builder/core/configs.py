# -*- coding: utf8 -*-

import os
import sys
import platform
import configparser
from . import colorconsole as cc

__all__ = ['cfg']


class AttrDict(dict):
    """
    可以像属性一样访问字典的 Key，var.key 等同于 var['key']
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            # print(self.__class__.__name__)
            raise

    def __setattr__(self, name, val):
        self[name] = val


class ConfigFile(AttrDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def init(self, cfg_file):
        self['ROOT_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

        self['py_exec'] = sys.executable

        _py_ver = platform.python_version_tuple()
        self['py_ver'] = _py_ver
        self['py_ver_str'] = '%s%s' % (_py_ver[0], _py_ver[1])
        self['is_py2'] = sys.version_info[0] == 2
        self['is_py3'] = sys.version_info[0] == 3

        _bits = platform.architecture()[0]
        if _bits == '64bit':
            self['is_x64'] = True
            self['is_x86'] = False
        else:
            self['is_x64'] = False
            self['is_x86'] = True

        _os = platform.system().lower()

        self['is_win'] = False
        self['is_linux'] = False
        self['is_macos'] = False
        self['dist'] = ''
        if _os == 'windows':
            self['is_win'] = True
            self['dist'] = 'windows'
        elif _os == 'linux':
            self['is_linux'] = True
            self['dist'] = 'linux'
        elif _os == 'darwin':
            self['is_macos'] = True
            self['dist'] = 'macos'
        else:
            cc.e('not support this OS: {}'.format(platform.system()))
            return False

        _cfg = configparser.ConfigParser()
        _cfg.read(cfg_file)
        if 'external_ver' not in _cfg.sections() or 'toolchain' not in _cfg.sections():
            cc.e('invalid configuration file: need `external_ver` and `toolchain` section.')
            return False

        _tmp = _cfg['external_ver']
        if 'libuv' not in _tmp or 'mbedtls' not in _tmp or 'sqlite' not in _tmp:
            cc.e('invalid configuration file: external version not set.')
            return False

        self['ver'] = AttrDict()
        for k in _tmp:
            self['ver'][k] = _tmp[k]

        _tmp = _cfg['toolchain']
        self['toolchain'] = AttrDict()
        if self.is_win:
            self['toolchain']['nsis'] = _tmp.get('nsis', None)
            self['toolchain']['msbuild'] = None  # msbuild always read from register.
        else:
            self['toolchain']['cmake'] = _tmp.get('cmake', '/usr/bin/cmake')

        return True


cfg = ConfigFile()
del ConfigFile
