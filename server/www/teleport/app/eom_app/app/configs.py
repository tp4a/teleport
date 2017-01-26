# -*- coding: utf-8 -*-

import os
# import sys
import configparser

from eom_common.eomcore.logger import *

__all__ = ['app_cfg']


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
        # self.__file_name = None
        # self.__save_indent = 0
        # self.__loaded = False

    def load(self, cfg_file):
        if not os.path.exists(cfg_file):
            log.e('configuration file does not exists: [{}]\n'.format(cfg_file))
            return False
        try:
            _cfg = configparser.ConfigParser()
            _cfg.read(cfg_file)
        except:
            log.e('can not load configuration file: [{}]\n'.format(cfg_file))
            return False

        if 'common' not in _cfg:
            log.e('invalid configuration file: [{}]\n'.format(cfg_file))
            return False

        _comm = _cfg['common']
        self['server_port'] = _comm.getint('port', 7190)
        self['log_file'] = _comm.get('log-file', None)
        if self['log_file'] is not None:
            self['log_path'] = os.path.dirname(self['log_file'])

        _level = _comm.getint('log-level', 2)
        if _level == 0:
            self['log_level'] = LOG_DEBUG
        elif _level == 1:
            self['log_level'] = LOG_VERBOSE
        elif _level == 2:
            self['log_level'] = LOG_INFO
        elif _level == 3:
            self['log_level'] = LOG_WARN
        elif _level == 4:
            self['log_level'] = LOG_ERROR
        else:
            self['log_level'] = LOG_VERBOSE

        log.set_attribute(min_level=self['log_level'])

        return True

_g_cfg = ConfigFile()
del ConfigFile


def app_cfg():
    global _g_cfg
    return _g_cfg


if __name__ == '__main__':
    cfg = ConfigFile()
