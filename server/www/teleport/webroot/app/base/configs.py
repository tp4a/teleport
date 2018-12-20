# -*- coding: utf-8 -*-

import configparser
import os
import json

from app.const import *
from .logger import log
from .utils import AttrDict, tp_convert_to_attr_dict, tp_make_dir

__all__ = ['tp_cfg']


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
        _name = name.replace('-', '_')
        if _name in self['_kvs']:
            return self['_kvs'][_name]
        else:
            if _name in self['_kvs']['_']:
                return self['_kvs']['_'][_name]
            else:
                return AttrDict()

    def __setattr__(self, key, val):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0].replace('-', '_')
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

    def reload(self):
        self['_cfg_default'] = {}
        self['_cfg_loaded'] = {}
        self['_kvs'] = {'_': self['_kvs']['_']}
        self._on_init()
        return self.load(self['_cfg_file'])

    def set_kv(self, key, val):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0].replace('-', '_')
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
            _key = x[0].replace('-', '_')
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
                    if sec_name in self['_cfg_default'] and _k in self['_cfg_default'][sec_name] and 'comment' in \
                            self['_cfg_default'][sec_name][_k]:
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
            _key = x[0].replace('-', '_')
        elif 2 == len(x):
            _sec = x[0].replace('-', '_')
            _key = x[1].replace('-', '_')
        else:
            return def_value, False

        if _sec not in self['_kvs']:
            return def_value, False
        if _key not in self['_kvs'][_sec]:
            return def_value, False

        if self['_kvs'][_sec][_key] is None:
            return def_value, False

        return str(self['_kvs'][_sec][_key]), True

    def get_int(self, key, def_value=-1):
        x = key.split('::')
        if 1 == len(x):
            _sec = '_'
            _key = x[0].replace('-', '_')
        elif 2 == len(x):
            _sec = x[0].replace('-', '_')
            _key = x[1].replace('-', '_')
        else:
            return def_value, False

        if _sec not in self['_kvs']:
            return def_value, False
        if _key not in self['_kvs'][_sec]:
            return def_value, False

        if self['_kvs'][_sec][_key] is None:
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
            _key = x[0].replace('-', '_')
        elif 2 == len(x):
            _sec = x[0].replace('-', '_')
            _key = x[1].replace('-', '_')
        else:
            return def_value, False

        if _sec not in self['_kvs']:
            return def_value, False
        if _key not in self['_kvs'][_sec]:
            return def_value, False

        if self['_kvs'][_sec][_key] is None:
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

        # 核心服务的配置信息，通过核心服务的接口获取
        self.core = AttrDict()
        self.core.detected = False

        # 系统默认配置，通过数据库查询得到
        self.sys = AttrDict()
        self.sys.loaded = False
        self.sys_smtp_password = ''  # 密码单独处理，避免无意中传递给前端页面了
        self.sys_ldap_password = ''

    def _on_init(self):
        self.set_default('common::ip', '0.0.0.0', 'ip=0.0.0.0')
        self.set_default('common::port', 7190,
                         'port listen by web server, default to 7190.\n'
                         'DO NOT FORGET update common::web-server-rpc in base.ini if you modified this setting.\n'
                         'port=7190')
        self.set_default('common::log-file', None,
                         'log file of web server, default to /var/log/teleport/tpweb.log\n'
                         'log-file=/var/log/teleport/tpweb.log'
                         )
        self.set_default('common::log-level', 2,
                         '`log-level` can be 0 ~ 4, default to 2.\n'
                         'LOG_LEVEL_DEBUG     0   log every-thing.\n'
                         'LOG_LEVEL_VERBOSE   1   log every-thing but without debug message.\n'
                         'LOG_LEVEL_INFO      2   log information/warning/error message.\n'
                         'LOG_LEVEL_WARN      3   log warning and error message.\n'
                         'LOG_LEVEL_ERROR     4   log error message only.\n'
                         'log-level=2'
                         )
        self.set_default('common::debug-mode', 0,
                         '0/1. default to 0.\n'
                         'in debug mode, `log-level` force to 0 and trace call stack when exception raised.\n'
                         'debug-mode=0'
                         )
        self.set_default('common::core-server-rpc', 'http://127.0.0.1:52080/rpc',
                         '`core-server-rpc` is the rpc interface of base server.\n'
                         'DO NOT FORGET update this setting if you modified rpc::bind-port in core.ini.\n'
                         'core-server-rpc=http://127.0.0.1:52080/rpc'
                         )
        self.set_default('database::type', 'sqlite',
                         'database in use, should be sqlite/mysql, default to sqlite.\n'
                         'type=sqlite'
                         )
        self.set_default('database::sqlite-file', None,
                         'sqlite-file=/var/lib/teleport/data/ts_db.db'
                         )
        self.set_default('database::mysql-host', '127.0.0.1', 'mysql-host=127.0.0.1')
        self.set_default('database::mysql-port', 3306, 'mysql-port=3306')
        self.set_default('database::mysql-db', 'teleport', 'mysql-db=teleport')
        self.set_default('database::mysql-prefix', 'tp_', 'mysql-prefix=tp_')
        self.set_default('database::mysql-user', 'teleport', 'mysql-user=teleport')
        self.set_default('database::mysql-password', 'password', 'mysql-password=password')

    def _on_get_save_info(self):
        return [
            {'common': ['ip', 'port', 'log-file', 'log-level', 'debug-mode', 'core-server-rpc']},
            {'database': ['type', 'sqlite-file', 'mysql-host', 'mysql-port', 'mysql-db', 'mysql-prefix', 'mysql-user',
                          'mysql-password']}
        ]

    def _on_load(self, cfg_parser):
        if 'common' not in cfg_parser:
            log.e('invalid config file, need `common` section.\n')
            return False
        if 'database' not in cfg_parser:
            log.e('invalid config file, need `database` section.\n')
            return False

        _sec = cfg_parser['common']

        _tmp_int = _sec.getint('log-level', -1)
        if log.LOG_DEBUG <= _tmp_int <= log.LOG_ERROR:
            self.set_kv('common::log-level', _tmp_int)
        log.set_attribute(min_level=self.common.log_level)

        _tmp_bool = _sec.getint('debug-mode', False)
        self.set_kv('common::debug-mode', _tmp_bool)
        if _tmp_bool:
            log.set_attribute(min_level=log.LOG_DEBUG, trace_error=log.TRACE_ERROR_FULL)

        _tmp_str = _sec.get('ip', None)
        if _tmp_str is not None:
            self.set_kv('common::ip', _tmp_str)

        _tmp_int = _sec.getint('port', -1)
        if -1 != _tmp_int:
            self.set_kv('common::port', _tmp_int)

        _tmp_str = _sec.get('log-file', None)
        if _tmp_str is not None:
            self.set_kv('common::log-file', _tmp_str)

        _tmp_str = _sec.get('core-server-rpc', None)
        if _tmp_str is not None:
            self.set_kv('common::core-server-rpc', _tmp_str)

        _sec = cfg_parser['database']

        _tmp_str = _sec.get('type', None)
        if _tmp_str is not None:
            self.set_kv('database::type', _tmp_str)

        _tmp_str = _sec.get('sqlite-file', None)
        if _tmp_str is not None:
            self.set_kv('database::sqlite-file', _tmp_str)

        _tmp_str = _sec.get('mysql-host', None)
        if _tmp_str is not None:
            self.set_kv('database::mysql-host', _tmp_str)

        _tmp_int = _sec.getint('mysql-port', -1)
        if _tmp_int != -1:
            self.set_kv('database::mysql-port', _tmp_int)

        _tmp_str = _sec.get('mysql-db', None)
        if _tmp_str is not None:
            self.set_kv('database::mysql-db', _tmp_str)

        _tmp_str = _sec.get('mysql-prefix', None)
        if _tmp_str is not None:
            self.set_kv('database::mysql-prefix', _tmp_str)

        _tmp_str = _sec.get('mysql-user', None)
        if _tmp_str is not None:
            self.set_kv('database::mysql-user', _tmp_str)

        _tmp_str = _sec.get('mysql-password', None)
        if _tmp_str is not None:
            self.set_kv('database::mysql-password', _tmp_str)

        _log_file, ok = self.get_str('common::log-file')
        if ok and _log_file:
            self.log_path = os.path.abspath(os.path.dirname(_log_file))
        else:
            _log_file = os.path.join(self.log_path, 'tpweb.log')
            self.set_default('common::log-file', _log_file)

        if not os.path.exists(self.log_path):
            tp_make_dir(self.log_path)
            if not os.path.exists(self.log_path):
                log.e('Can not create log path:{}\n'.format(self.log_path))
                return False

        log.set_attribute(filename=_log_file)

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
            log.e('invalid core server config.\n')
            return False

        return True

    def update_sys(self, conf_data):
        self.sys = AttrDict()
        self.sys.loaded = False

        if conf_data is None:
            log.w('system default config info is empty.\n')
            # return True
        
        # =====================================
        # 全局设置相关
        # =====================================
        try:
            _glob = json.loads(conf_data['global'])
        except:
            log.w('password config not set or invalid, use default.\n')
            _glob = {}

        self.sys.glob = tp_convert_to_attr_dict(_glob)
        if not self.sys.glob.is_exists('url_proto'):
            self.sys.glob.url_proto = False
        
        # =====================================
        # 密码策略相关
        # =====================================
        try:
            _password = json.loads(conf_data['password'])
        except:
            log.w('password config not set or invalid, use default.\n')
            _password = {}

        self.sys.password = tp_convert_to_attr_dict(_password)
        if not self.sys.password.is_exists('allow_reset'):
            self.sys.password.allow_reset = True
        if not self.sys.password.is_exists('force_strong'):
            self.sys.password.force_strong = True
        if not self.sys.password.is_exists('timeout'):
            self.sys.password.timeout = 0

        # =====================================
        # 登录相关
        # =====================================
        try:
            _login = json.loads(conf_data['login'])
        except:
            log.w('login config not set or invalid, use default.\n')
            _login = {}

        self.sys.login = tp_convert_to_attr_dict(_login)
        if not self.sys.login.is_exists('session_timeout'):
            self.sys.login.session_timeout = 60  # 1 hour
        if not self.sys.login.is_exists('retry'):
            self.sys.login.retry = 0
        if not self.sys.login.is_exists('lock_timeout'):
            self.sys.login.lock_timeout = 30  # 30 min
        if not self.sys.login.is_exists('auth'):
            # self.sys.login.auth = TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA | TP_LOGIN_AUTH_USERNAME_OATH | TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH
            self.sys.login.auth = TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA | TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH

        # =====================================
        # 连接控制相关
        # =====================================
        try:
            _sess = json.loads(conf_data['session'])
        except:
            log.w('session config not set or invalid, use default.\n')
            _sess = {}

        self.sys.session = tp_convert_to_attr_dict(_sess)
        if not self.sys.session.is_exists('noop_timeout'):
            self.sys.session.noop_timeout = 15  # 15 minute
        if not self.sys.session.is_exists('flag_record'):
            self.sys.session.flag_record = TP_FLAG_ALL  # TP_FLAG_RECORD_REPLAY | TP_FLAG_RECORD_REAL_TIME
        if not self.sys.session.is_exists('flag_rdp'):
            self.sys.session.flag_rdp = TP_FLAG_ALL  # TP_FLAG_RDP_DESKTOP | TP_FLAG_RDP_CLIPBOARD | TP_FLAG_RDP_DISK | TP_FLAG_RDP_CONSOLE
        if not self.sys.session.is_exists('flag_ssh'):
            self.sys.session.flag_ssh = TP_FLAG_ALL  # TP_FLAG_SSH_SHELL | TP_FLAG_SSH_SFTP

        # =====================================
        # SMTP相关
        # =====================================
        self.sys_smtp_password = ''
        try:
            _smtp = json.loads(conf_data['smtp'])
        except:
            log.w('smtp config not set or invalid, use default.\n')
            _smtp = {}

        self.sys.smtp = tp_convert_to_attr_dict(_smtp)
        if not self.sys.smtp.is_exists('server'):
            self.sys.smtp.server = ''
        if not self.sys.smtp.is_exists('port'):
            self.sys.smtp.port = 25
        if not self.sys.smtp.is_exists('ssl'):
            self.sys.smtp.ssl = False
        if not self.sys.smtp.is_exists('sender'):
            self.sys.smtp.sender = ''
        if self.sys.smtp.is_exists('password'):
            self.sys_smtp_password = self.sys.smtp.password
            self.sys.smtp.password = '********'

        # =====================================
        # 存储相关
        # =====================================
        try:
            _storage = json.loads(conf_data['storage'])
        except:
            log.w('storage config not set or invalid, use default.\n')
            _storage = {}

        self.sys.storage = tp_convert_to_attr_dict(_storage)
        if not self.sys.storage.is_exists('keep_log'):
            self.sys.storage.keep_log = 0
        if not self.sys.storage.is_exists('keep_record'):
            self.sys.storage.keep_record = 0
        if not self.sys.storage.is_exists('cleanup_hour'):
            self.sys.storage.cleanup_hour = 4
        if not self.sys.storage.is_exists('cleanup_minute'):
            self.sys.storage.cleanup_minute = 30

        # =====================================
        # LDAP相关
        # =====================================
        self.sys_ldap_password = ''
        try:
            _ldap = json.loads(conf_data['ldap'])
        except:
            log.w('ldap config not set or invalid, use default.\n')
            _ldap = {}

        self.sys.ldap = tp_convert_to_attr_dict(_ldap)
        if not self.sys.ldap.is_exists('server'):
            self.sys.ldap.server = ''
        if not self.sys.ldap.is_exists('port'):
            self.sys.ldap.port = 389
        if not self.sys.ldap.is_exists('domain'):
            self.sys.ldap.domain = ''
        if not self.sys.ldap.is_exists('admin'):
            self.sys.ldap.admin = ''
        if not self.sys.ldap.is_exists('base_dn'):
            self.sys.ldap.base_dn = ''
        if not self.sys.ldap.is_exists('filter'):
            self.sys.ldap.filter = ''
        if not self.sys.ldap.is_exists('attr_username'):
            self.sys.ldap.attr_username = ''
        if not self.sys.ldap.is_exists('attr_surname'):
            self.sys.ldap.attr_surname = ''
        if not self.sys.ldap.is_exists('attr_email'):
            self.sys.ldap.attr_email = ''
        if self.sys.ldap.is_exists('password'):
            self.sys_ldap_password = self.sys.ldap.password
            self.sys.ldap.password = '********'

        self.sys.loaded = True

        return True


def tp_cfg():
    """
    :rtype: app.base.configs.AppConfig
    """
    import builtins
    if '__app_cfg__' not in builtins.__dict__:
        builtins.__dict__['__app_cfg__'] = AppConfig()
    return builtins.__dict__['__app_cfg__']

# def app_cfg():
#     import builtins
#     if '__web_config__' not in builtins.__dict__:
#         builtins.__dict__['__web_config__'] = ConfigFile()
#     return builtins.__dict__['__web_config__']


# if __name__ == '__main__':
#     cfg = AppConfig()
#     cfg.set_default('common::log-file', 'E:/test/log/web.log')
#     cfg.load('E:/test/config/web.ini')
#     cfg.aaa = 'this is aaa'
#     cfg.bbb = 123
#     cfg.ccc = False
#
#     print('----usage--------------------')
#     print(cfg.common.port)
#     print(cfg.get_str('aaa'))
#     print(cfg.get_str('bbb'))
#     print(cfg.get_str('ccc'))
#     print('----usage--------------------')
#     print(cfg.get_int('aaa'))
#     print(cfg.get_int('bbb'))
#     print(cfg.get_int('ccc'))
#     print('----usage--------------------')
#     print(cfg.get_bool('aaa'))
#     print(cfg.get_bool('bbb'))
#     print(cfg.get_bool('ccc'))
#     print('----usage--------------------')
#     print(cfg.common)
#     print('----usage--------------------')
#     print(cfg.aaa)
#     print(cfg.bbb)
#     print(cfg.ccc)
#
#     cfg.save('E:/test/config/web-new.ini')
#     cfg.save()
