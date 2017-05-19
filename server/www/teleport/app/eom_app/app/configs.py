# -*- coding: utf-8 -*-

import configparser
import os

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
            return None

    def __setattr__(self, name, val):
        self[name] = val


class ConfigFile(AttrDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        import builtins
        if '__web_config__' in builtins.__dict__:
            raise RuntimeError('WebConfig object exists, you can not create more than one instance.')

        self['core'] = AttrDict()
        self['core']['detected'] = False
        # self['core']['ssh'] = AttrDict()
        # self['core']['ssh']['enable'] = False
        # self['core']['ssh']['port'] = 0  # 52189
        # self['core']['rdp'] = AttrDict()
        # self['core']['rdp']['enable'] = False
        # self['core']['rdp']['port'] = 0  # 52089
        # self['core']['telnet'] = AttrDict()
        # self['core']['telnet']['enable'] = False
        # self['core']['telnet']['port'] = 0  # 52389

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

        self['log_level'] = log.LOG_INFO
        _level = _comm.getint('log-level', 2)
        if _level == 0:
            self['log_level'] = log.LOG_DEBUG
        elif _level == 1:
            self['log_level'] = log.LOG_VERBOSE
        elif _level == 2:
            self['log_level'] = log.LOG_INFO
        elif _level == 3:
            self['log_level'] = log.LOG_WARN
        elif _level == 4:
            self['log_level'] = log.LOG_ERROR
        else:
            self['log_level'] = log.LOG_VERBOSE

        # log.set_attribute(min_level=self['log_level'])

        self['debug'] = False
        _debug = _comm.getint('debug', 0)
        if _debug == 1:
            self['log_level'] = log.LOG_DEBUG
            self['debug'] = True

        self['core_server_rpc'] = _comm.get('core-server-rpc', 'http://127.0.0.1:52080/rpc')

        return True

    def update_core(self, conf_data):
        # log.d('update core server config info.\n')
        self['core'] = AttrDict()

        if conf_data is None:
            log.w('core server config info is empty.\n')
            self['core']['detected'] = False
            return True

        try:
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

            if 'replay-path' in conf_data:
                self['core']['replay_path'] = conf_data['replay-path']

            if 'web-server-rpc' in conf_data:
                self['core']['web_server_rpc'] = conf_data['web-server-rpc']
            if 'version' in conf_data:
                self['core']['version'] = conf_data['version']

            self['core']['detected'] = True

        except IndexError:
            log.e('invalid core config.\n')
            return False

        return True


class BaseAppConfig(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        import builtins
        if '__app_cfg__' in builtins.__dict__:
            raise RuntimeError('AppConfig instance already exists.')

        self['_cfg_default'] = {}
        self['_cfg_loaded'] = {}
        self['_kvs'] = {'_': AttrDict()}
        self['_cfg_file'] = ''

        self._on_init()

    def __getattr__(self, name):
        if name in self['_kvs']:
            return self['_kvs'][name]
        else:
            if name in self['_kvs']['_']:
                return self['_kvs']['_'][name]
            else:
                return AttrDict()

    def __setattr__(self, key, val):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0]
        elif 2 == len(x):
            _sec = x[0].replace('-', '_')
            _key = x[1].replace('-', '_')
        else:
            raise RuntimeError('invalid name.')

        if _sec not in self['_kvs']:
            self['_kvs'][_sec] = {}
        self['_kvs'][_sec][_key] = val

    def _on_init(self):
        raise RuntimeError('can not create instance for base class.')

    def _on_get_save_info(self):
        raise RuntimeError('can not create instance for base class.')

    def _on_load(self, cfg_parser):
        raise RuntimeError('can not create instance for base class.')

    def set_kv(self, key, val):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0]
        elif 2 == len(x):
            _sec = x[0].replace('-', '_')
            _key = x[1].replace('-', '_')
        else:
            raise RuntimeError('invalid name.')

        if _sec not in self['_cfg_loaded']:
            self['_cfg_loaded'][_sec] = {}
        self['_cfg_loaded'][_sec][_key] = val
        self._update_kvs(_sec, _key, val)

    def set_default(self, key, val, comment=None):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0]
        elif 2 == len(x):
            _sec = x[0].replace('-', '_')
            _key = x[1].replace('-', '_')
        else:
            raise RuntimeError('invalid name.')

        if _sec not in self['_cfg_default']:
            self['_cfg_default'][_sec] = {}
        if _key not in self['_cfg_default'][_sec]:
            self['_cfg_default'][_sec][_key] = {}
            self['_cfg_default'][_sec][_key]['value'] = val
            self['_cfg_default'][_sec][_key]['comment'] = comment
        else:
            self['_cfg_default'][_sec][_key]['value'] = val

            if comment is not None:
                self['_cfg_default'][_sec][_key]['comment'] = comment
            elif 'comment' not in self['_cfg_default'][_sec][_key]:
                self['_cfg_default'][_sec][_key]['comment'] = None

        self._update_kvs(_sec, _key, val)

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

        if not self._on_load(_cfg):
            return False

        self['_cfg_file'] = cfg_file
        return True

    def save(self, cfg_file=None):
        if cfg_file is None:
            cfg_file = self['_cfg_file']
        _save = self._on_get_save_info()

        cnt = ['; codec: utf-8\n']

        is_first_section = True
        for sections in _save:
            for sec_name in sections:
                sec_name = sec_name.replace('-', '_')
                if sec_name in self['_cfg_default'] or sec_name in self['_cfg_loaded']:
                    if not is_first_section:
                        cnt.append('\n')
                    cnt.append('[{}]'.format(sec_name))
                    is_first_section = False
                for k in sections[sec_name]:
                    _k = k.replace('-', '_')
                    have_comment = False
                    if sec_name in self['_cfg_default'] and _k in self['_cfg_default'][sec_name] and 'comment' in self['_cfg_default'][sec_name][_k]:
                        comments = self['_cfg_default'][sec_name][_k]['comment']
                        if comments is not None:
                            comments = self['_cfg_default'][sec_name][_k]['comment'].split('\n')
                            cnt.append('')
                            have_comment = True
                            for comment in comments:
                                cnt.append('; {}'.format(comment))

                    if sec_name in self['_cfg_loaded'] and _k in self['_cfg_loaded'][sec_name]:
                        if not have_comment:
                            cnt.append('')
                        cnt.append('{}={}'.format(k, self['_cfg_loaded'][sec_name][_k]))

        cnt.append('\n')
        tmp_file = '{}.tmp'.format(cfg_file)

        try:
            with open(tmp_file, 'w', encoding='utf8') as f:
                f.write('\n'.join(cnt))
            if os.path.exists(cfg_file):
                os.unlink(cfg_file)
            os.rename(tmp_file, cfg_file)
            return True
        except Exception as e:
            print(e.__str__())
            return False

    def _update_kvs(self, section, key, val):
        if section not in self['_kvs']:
            self['_kvs'][section] = AttrDict()
        self['_kvs'][section][key] = val

    def get_str(self, key, def_value=None):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0]
        elif 2 == len(x):
            _sec = x[0]
            _key = x[1]
        else:
            return def_value, False

        if _sec not in self['_kvs']:
            return def_value, False
        if _key not in self['_kvs'][_sec]:
            return def_value, False
        return str(self['_kvs'][_sec][_key]), True

    def get_int(self, key, def_value=-1):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0]
        elif 2 == len(x):
            _sec = x[0]
            _key = x[1]
        else:
            return def_value, False

        if _sec not in self['_kvs']:
            return def_value, False
        if _key not in self['_kvs'][_sec]:
            return def_value, False

        try:
            return int(self['_kvs'][_sec][_key]), True
        except ValueError as e:
            print(e.__str__())
            return def_value, False

    def get_bool(self, key, def_value=False):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0]
        elif 2 == len(x):
            _sec = x[0]
            _key = x[1]
        else:
            return def_value, False

        if _sec not in self['_kvs']:
            return def_value, False
        if _key not in self['_kvs'][_sec]:
            return def_value, False

        tmp = str(self['_kvs'][_sec][_key]).lower()

        if tmp in ['yes', 'true', '1']:
            return True, True
        elif tmp in ['no', 'false', '0']:
            return False, True
        else:
            return def_value, False


class AppConfig(BaseAppConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.core = AttrDict()
        self.core.detected = False

    def _on_init(self):
        self.set_default('common::ip', '0.0.0.0', 'ip=0.0.0.0')
        self.set_default('common::port', 7190, 'port=7190')
        self.set_default('common::log-file', None,
                         '`log-file` define the log file location. if not set, default location\n'
                         'to %APPROOT%/log/web.log\n'
                         'log-file=/var/log/teleport/tpweb.log'
                         )
        self.set_default('common::log-level', 2,
                         '`log-level` can be 0 ~ 4, default to 2.\n'
                         'LOG_LEVEL_DEBUG     0   log every-thing.\n'
                         'LOG_LEVEL_VERBOSE   1   log every-thing but without debug message.\n'
                         'LOG_LEVEL_INFO      2   log information/warning/error message.\n'
                         'LOG_LEVEL_WARN      3   log warning and error message.\n'
                         'LOG_LEVEL_ERROR     4   log error message only.'
                         )
        self.set_default('common::debug-mode', 0,
                         'default to `no`.\n'
                         'in debug mode, `log-level` force to 0 and trace call stack when exception raised.'
                         )
        self.set_default('common::core-server-rpc', 'http://127.0.0.1:52080/rpc',
                         '`core-server-rpc` is the rpc interface of core server.\n'
                         'DO NOT FORGET update this setting if you modified rpc::bind-port in core.ini.'
                         )

    def _on_get_save_info(self):
        return [
            {'common': ['ip', 'port', 'log-file', 'log-level', 'debug-mode', 'core-server-rpc']},
        ]

    def _on_load(self, cfg_parser):
        if 'common' not in cfg_parser:
            return False

        _comm = cfg_parser['common']

        _tmp_int = _comm.getint('log-level', -1)
        if log.LOG_DEBUG <= _tmp_int <= log.LOG_ERROR:
            self.set_kv('common::log-level', _tmp_int)
        log.set_attribute(min_level=self.common.log_level)

        _tmp_bool = _comm.getint('debug-mode', False)
        self.set_kv('common::debug-mode', _tmp_bool)
        if _tmp_bool:
            log.set_attribute(min_level=log.LOG_DEBUG, trace_error=log.TRACE_ERROR_FULL)

        _tmp_str = _comm.get('ip', '0.0.0.0')
        if _tmp_str is not None:
            self.set_kv('common::ip', _tmp_str)

        _tmp_int = _comm.getint('port', -1)
        if -1 != _tmp_int:
            self.set_kv('common::port', _tmp_int)

        _tmp_str = _comm.get('log-file', None)
        if _tmp_str is not None:
            self.set_kv('common::log-file', _tmp_str)

        return True

    def update_core(self, conf_data):
        self.core = AttrDict()
        self.core.detected = False

        if conf_data is None:
            log.w('core server config info is empty.\n')
            return True

        try:
            self.core.ssh = AttrDict()
            self.core.ssh.enable = False
            self.core.ssh.port = 52189
            if 'ssh' in conf_data:
                self.core.ssh.enable = conf_data['ssh']['enable']
                self.core.ssh.port = conf_data['ssh']['port']

            self.core.rdp = AttrDict()
            self.core.rdp.enable = False
            self.core.rdp.port = 52089
            if 'rdp' in conf_data:
                self.core.rdp.enable = conf_data['rdp']['enable']
                self.core.rdp.port = conf_data['rdp']['port']

            self.core.telnet = AttrDict()
            self.core.telnet.enable = False
            self.core.telnet.port = 52389
            if 'telnet' in conf_data:
                self.core.telnet.enable = conf_data['telnet']['enable']
                self.core.telnet.port = conf_data['telnet']['port']

            if 'replay-path' in conf_data:
                self.core.replay_path = conf_data['replay-path']

            if 'web-server-rpc' in conf_data:
                self.core.web_server_rpc = conf_data['web-server-rpc']
            if 'version' in conf_data:
                self.core.version = conf_data['version']

            self.core.detected = True

        except IndexError:
            log.e('invalid core config.\n')
            return False

        return True

def app_cfg():
    import builtins
    if '__app_cfg__' not in builtins.__dict__:
        builtins.__dict__['__app_cfg__'] = AppConfig()
    return builtins.__dict__['__app_cfg__']


# def app_cfg():
#     import builtins
#     if '__web_config__' not in builtins.__dict__:
#         builtins.__dict__['__web_config__'] = ConfigFile()
#     return builtins.__dict__['__web_config__']


if __name__ == '__main__':
    cfg = AppConfig()
    cfg.set_default('common::log-file', 'E:/test/log/web.log')
    cfg.load('E:/test/config/web.ini')
    cfg.aaa = 'this is aaa'
    cfg.bbb = 123
    cfg.ccc = False

    print('----usage--------------------')
    print(cfg.common.port)
    print(cfg.get_str('aaa'))
    print(cfg.get_str('bbb'))
    print(cfg.get_str('ccc'))
    print('----usage--------------------')
    print(cfg.get_int('aaa'))
    print(cfg.get_int('bbb'))
    print(cfg.get_int('ccc'))
    print('----usage--------------------')
    print(cfg.get_bool('aaa'))
    print(cfg.get_bool('bbb'))
    print(cfg.get_bool('ccc'))
    print('----usage--------------------')
    print(cfg.common)
    print('----usage--------------------')
    print(cfg.aaa)
    print(cfg.bbb)
    print(cfg.ccc)

    cfg.save('E:/test/config/web-new.ini')
    cfg.save()
