# -*- coding: utf-8 -*-

import configparser
import os

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
            return None

    def __setattr__(self, name, val):
        self[name] = val


class ConfigFile(AttrDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self['core'] = AttrDict()
        self['core']['ssh'] = AttrDict()
        self['core']['ssh']['enable'] = False
        self['core']['ssh']['port'] = 52189
        self['core']['rdp'] = AttrDict()
        self['core']['rdp']['enable'] = False
        self['core']['rdp']['port'] = 52089
        self['core']['telnet'] = AttrDict()
        self['core']['telnet']['enable'] = False
        self['core']['telnet']['port'] = 52389

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

        self['log_level'] = LOG_INFO
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

        # log.set_attribute(min_level=self['log_level'])

        self['debug'] = False
        _debug = _comm.getint('debug', 0)
        if _debug == 1:
            self['log_level'] = LOG_DEBUG
            self['debug'] = True

        self['core_server_rpc'] = _comm.get('core-server-rpc', 'http://127.0.0.1:52080/rpc')

        return True

    def update_core(self, conf_data):
        try:
            self['core'] = AttrDict()

            self['core']['ssh'] = AttrDict()
            self['core']['ssh']['enable'] = False
            self['core']['ssh']['port'] = 52189
            if 'ssh' in conf_data:
                self['core']['ssh']['enable'] = conf_data['ssh']['enable']
                self['core']['ssh']['port'] = conf_data['ssh']['port']

            self['core']['rdp'] = AttrDict()
            self['core']['rdp']['enable'] = False
            self['core']['rdp']['port'] = 52089
            if 'rdp' in conf_data:
                self['core']['rdp']['enable'] = conf_data['rdp']['enable']
                self['core']['rdp']['port'] = conf_data['rdp']['port']

            self['core']['telnet'] = AttrDict()
            self['core']['telnet']['enable'] = False
            self['core']['telnet']['port'] = 52389
            if 'telnet' in conf_data:
                self['core']['telnet']['enable'] = conf_data['telnet']['enable']
                self['core']['telnet']['port'] = conf_data['telnet']['port']

            self['core']['replay_path'] = conf_data['replay-path']

        except IndexError:
            log.e('invalid core config.\n')
            return False

        return True


_g_cfg = ConfigFile()
del ConfigFile


def app_cfg():
    global _g_cfg
    return _g_cfg


if __name__ == '__main__':
    cfg = ConfigFile()
