# -*- coding: utf8 -*-

import os
import sys
import platform
from . import colorconsole as cc

__all__ = ['cfg']


class TpDict(dict):
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


class ConfigFile(TpDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.__file_name = None
        # self.__save_indent = 0
        # self.__loaded = False

    def init(self, cfg_file):
        if not self.load(cfg_file, True):
            return False

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

        self['dist'] = ''
        if _os == 'windows':
            self['dist'] = 'windows'
        elif _os == 'linux':
            self['dist'] = 'linux'
        elif _os == 'darwin':
            self['dist'] = 'macos'
        else:
            cc.e('not support this OS: {}'.format(platform.system()))
            return False

        return True

    def load_str(self, module, code):
        m = type(sys)(module)
        m.__module_class__ = type(sys)
        m.__file__ = module

        try:
            exec(compile(code, module, 'exec'), m.__dict__)
        except Exception as e:
            cc.e('%s\n' % str(e))
            # print(str(e))
            # if eom_dev_conf.debug:
            #     raise
            return False

        for y in m.__dict__:
            if '__' == y[:2]:
                continue
            if isinstance(m.__dict__[y], dict):
                self[y] = TpDict()
                self._assign_dict(m.__dict__[y], self[y])
            else:
                self[y] = m.__dict__[y]

        return True

    def load(self, full_path, must_exists=True):
        try:
            f = open(full_path, encoding='utf8')
            code = f.read()
            f.close()
            self.__loaded = True
        except IOError:
            if must_exists:
                cc.e('Can not load config file: %s\n' % full_path)
            return False

        module = os.path.basename(full_path)
        if not self.load_str(module, code):
            return False

        self.__file_name = full_path
        return True

    def _assign_dict(self, _from, _to):
        for y in _from:
            if isinstance(_from[y], dict):
                _to[y] = TpDict()
                self._assign_dict(_from[y], _to[y])
            else:
                _to[y] = _from[y]


cfg = ConfigFile()
del ConfigFile
