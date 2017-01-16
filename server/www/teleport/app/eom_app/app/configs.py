# -*- coding: utf-8 -*-

import os
import sys
import configparser

from eom_common.eomcore.logger import log

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


# def attr_dict(obj):
#     """
#     将一个对象中的dict转变为AttrDict类型
#     """
#     if isinstance(obj, dict):
#         ret = AttrDict()
#         for k in obj:
#             # ret[k] = obj[k]
#             if isinstance(obj[k], dict):
#                 ret[k] = attr_dict(obj[k])
#             else:
#                 ret[k] = obj[k]
#     else:
#         ret = obj
#     return ret


class ConfigFile(AttrDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.__file_name = None
        # self.__save_indent = 0
        # self.__loaded = False

    def load(self, cfg_file):
        if not os.path.exists(cfg_file):
            log.e('configuration file does not exists.')
            return False
        try:
            _cfg = configparser.ConfigParser()
            _cfg.read(cfg_file)
        except:
            log.e('can not load configuration file.')
            return False

        if 'common' not in _cfg:
            log.e('invalid configuration file.')
            return False

        _comm = _cfg['common']
        self['server_port'] = _comm.getint('port', 7190)
        self['log_file'] = _comm.get('log-file', None)
        if self['log_file'] is not None:
            self['log_path'] = os.path.dirname(self['log_file'])

        return True

    # def load_str(self, module, code):
    #     m = type(sys)(module)
    #     m.__module_class__ = type(sys)
    #     m.__file__ = module
    #
    #     try:
    #         exec(compile(code, module, 'exec'), m.__dict__)
    #     except Exception as e:
    #         log.e('%s\n' % str(e))
    #         # print(str(e))
    #         # if eom_dev_conf.debug:
    #         #     raise
    #         return False
    #
    #     for y in m.__dict__:
    #         if '__' == y[:2]:
    #             continue
    #         if isinstance(m.__dict__[y], dict):
    #             self[y] = AttrDict()
    #             self._assign_dict(m.__dict__[y], self[y])
    #         else:
    #             self[y] = m.__dict__[y]
    #
    #     return True
    #
    # def _load(self, full_path, must_exists=True):
    #     try:
    #         f = open(full_path, encoding='utf8')
    #         code = f.read()
    #         f.close()
    #         self.__loaded = True
    #     except IOError:
    #         if must_exists:
    #             log.e('Can not load config file: %s\n' % full_path)
    #         return False
    #
    #     module = os.path.basename(full_path)
    #     if not self.load_str(module, code):
    #         return False
    #
    #     self.__file_name = full_path
    #     return True
    #
    # def _assign_dict(self, _from, _to):
    #     for y in _from:
    #         if isinstance(_from[y], dict):
    #             _to[y] = AttrDict()
    #             self._assign_dict(_from[y], _to[y])
    #         else:
    #             _to[y] = _from[y]
    #

_g_cfg = ConfigFile()
del ConfigFile


def app_cfg():
    global _g_cfg
    return _g_cfg


if __name__ == '__main__':
    cfg = ConfigFile()
