# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import shutil

import app.model.system as system_model
import tornado.gen
from app.app_ver import TP_SERVER_VER
from app.base import mail
from app.base.configs import tp_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.logger import *
from app.const import *
from app.base.db import get_db
from app.model import syslog
from app.model import record
from app.model import ops
from app.model import audit
from app.model import user
from app.base.core_server import core_service_async_post_http
from app.base.session import tp_session
from app.logic.auth.ldap import Ldap


class DoGetTimeHandler(TPBaseJsonHandler):
    def post(self):
        time_now = int(datetime.datetime.utcnow().timestamp())
        self.write_json(TPE_OK, data=time_now)


class ConfigHandler(TPBaseHandler):
    @tornado.gen.coroutine
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        cfg = tp_cfg()

        # core_detected = False
        req = {'method': 'get_config', 'param': []}
        _yr = core_service_async_post_http(req)
        code, ret_data = yield _yr
        if code != TPE_OK:
            cfg.update_core(None)
        else:
            cfg.update_core(ret_data)

        if not tp_cfg().core.detected:
            total_size = 0
            free_size = 0
        else:
            total_size, _, free_size = shutil.disk_usage(tp_cfg().core.replay_path)

        _db = get_db()
        db = {'type': _db.db_type}
        if _db.db_type == _db.DB_TYPE_SQLITE:
            db['sqlite_file'] = _db.sqlite_file
        elif _db.db_type == _db.DB_TYPE_MYSQL:
            db['mysql_host'] = _db.mysql_host
            db['mysql_port'] = _db.mysql_port
            db['mysql_db'] = _db.mysql_db
            db['mysql_user'] = _db.mysql_user

        param = {
            'total_size': total_size,
            'free_size': free_size,
            'core_cfg': tp_cfg().core,
            'sys_cfg': tp_cfg().sys,
            'web_cfg': {
                'version': TP_SERVER_VER,
                'core_server_rpc': tp_cfg().common.core_server_rpc,
                'db': db
            }
        }

        self.render('system/config.mako', page_param=json.dumps(param))


class RoleHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_ROLE)
        if ret != TPE_OK:
            return
        self.render('system/role.mako')


class DoRoleUpdateHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_ROLE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            role_id = int(args['role_id'])
            role_name = args['role_name']
            privilege = int(args['privilege'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if role_id == 0:
            err, role_id = system_model.add_role(self, role_name, privilege)
        else:
            if role_id == 1:
                return self.write_json(TPE_FAILED, '禁止修改系统管理员角色！')
            err = system_model.update_role(self, role_id, role_name, privilege)

        return self.write_json(err, data=role_id)


class DoRoleRemoveHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_ROLE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            role_id = int(args['role_id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if role_id == 1:
            return self.write_json(TPE_FAILED, '禁止删除系统管理员角色！')
        err = system_model.remove_role(self, role_id)

        return self.write_json(err)


class SysLogHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_LOG)
        if ret != TPE_OK:
            return
        self.render('system/syslog.mako')


class DoGetLogsHandler(TPBaseJsonHandler):
    def post(self):
        # return self.write_json(0, data=[])

        filter = dict()
        order = dict()
        order['name'] = 'log_time'
        order['asc'] = False
        limit = dict()
        limit['page_index'] = 0
        limit['per_page'] = 25

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)

            tmp = list()
            _filter = args['filter']
            if _filter is not None:
                for i in _filter:
                    if i == 'user_name':
                        _x = _filter[i].strip()
                        if _x == '全部':
                            tmp.append(i)

                    if i == 'search':
                        _x = _filter[i].strip()
                        if len(_x) == 0:
                            tmp.append(i)
                        continue

                for i in tmp:
                    del _filter[i]

                filter.update(_filter)

        _limit = args['limit']
        if _limit['page_index'] < 0:
            _limit['page_index'] = 0
        if _limit['per_page'] < 10:
            _limit['per_page'] = 10
        if _limit['per_page'] > 100:
            _limit['per_page'] = 100

        limit.update(_limit)

        _order = args['order']
        if _order is not None:
            order['name'] = _order['k']
            order['asc'] = _order['v']

        err, total, record_list = syslog.get_logs(filter, order, _limit)
        if err != TPE_OK:
            return self.write_json(err)
        ret = dict()
        ret['page_index'] = limit['page_index']
        ret['total'] = total
        ret['data'] = record_list

        return self.write_json(0, data=ret)


class DoSaveCfgHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            processed = False
            if 'smtp' in args:
                processed = True
                _cfg = args['smtp']
                _server = _cfg['server']
                _port = _cfg['port']
                _ssl = _cfg['ssl']
                _sender = _cfg['sender']
                _password = _cfg['password']

                # TODO: encrypt the password before save by core-service.
                # TODO: if not send password, use pre-saved password.

                err = system_model.save_config(self, '更新SMTP设置', 'smtp', _cfg)
                if err == TPE_OK:
                    # 同时更新内存缓存
                    tp_cfg().sys.smtp.server = _server
                    tp_cfg().sys.smtp.port = _port
                    tp_cfg().sys.smtp.ssl = _ssl
                    tp_cfg().sys.smtp.sender = _sender
                    # 特殊处理，防止前端拿到密码
                    tp_cfg().sys_smtp_password = _password
                else:
                    return self.write_json(err)            
            
            #增加urlprotocol的配置		
            if 'global' in args:
                processed = True
                _cfg = args['global']
                _url_proto = _cfg['url_proto']
                
                err = system_model.save_config(self, '更新全局设置', 'global', _cfg)
                if err == TPE_OK:
                    tp_cfg().sys.glob.url_proto = _url_proto
                else:
                    return self.write_json(err)
            

            if 'password' in args:
                processed = True
                _cfg = args['password']
                _allow_reset = _cfg['allow_reset']
                _force_strong = _cfg['force_strong']
                _timeout = _cfg['timeout']
                err = system_model.save_config(self, '更新密码策略设置', 'password', _cfg)
                if err == TPE_OK:
                    tp_cfg().sys.password.allow_reset = _allow_reset
                    tp_cfg().sys.password.force_strong = _force_strong
                    tp_cfg().sys.password.timeout = _timeout
                else:
                    return self.write_json(err)

            if 'login' in args:
                processed = True
                _cfg = args['login']
                _session_timeout = _cfg['session_timeout']
                _retry = _cfg['retry']
                _lock_timeout = _cfg['lock_timeout']
                _auth = _cfg['auth']
                err = system_model.save_config(self, '更新登录策略设置', 'login', _cfg)
                if err == TPE_OK:
                    tp_cfg().sys.login.session_timeout = _session_timeout
                    tp_cfg().sys.login.retry = _retry
                    tp_cfg().sys.login.lock_timeout = _lock_timeout
                    tp_cfg().sys.login.auth = _auth
                    tp_session().update_default_expire()
                else:
                    return self.write_json(err)

            if 'session' in args:
                processed = True
                _cfg = args['session']
                _noop_timeout = _cfg['noop_timeout']
                _flag_record = _cfg['flag_record']
                _flag_rdp = _cfg['flag_rdp']
                _flag_ssh = _cfg['flag_ssh']
                err = system_model.save_config(self, '更新连接控制设置', 'session', _cfg)
                if err == TPE_OK:
                    try:
                        req = {'method': 'set_config', 'param': {'noop_timeout': _noop_timeout}}
                        _yr = core_service_async_post_http(req)
                        code, ret_data = yield _yr
                        if code != TPE_OK:
                            log.e('can not set runtime-config to core-server.\n')
                            return self.write_json(code)
                    except:
                        pass

                    tp_cfg().sys.session.noop_timeout = _noop_timeout
                    tp_cfg().sys.session.flag_record = _flag_record
                    tp_cfg().sys.session.flag_rdp = _flag_rdp
                    tp_cfg().sys.session.flag_ssh = _flag_ssh
                else:
                    return self.write_json(err)

            if 'storage' in args:
                processed = True
                _cfg = args['storage']
                _keep_log = _cfg['keep_log']
                _keep_record = _cfg['keep_record']
                _cleanup_hour = _cfg['cleanup_hour']
                _cleanup_minute = _cfg['cleanup_minute']

                if not ((30 <= _keep_log <= 365) or _keep_log == 0):
                    return self.write_json(TPE_PARAM, '系统日志保留时间超出范围！')
                if not ((30 <= _keep_record <= 365) or _keep_record == 0):
                    return self.write_json(TPE_PARAM, '会话录像保留时间超出范围！')

                err = system_model.save_config(self, '更新存储策略设置', 'storage', _cfg)
                if err == TPE_OK:
                    tp_cfg().sys.storage.keep_log = _keep_log
                    tp_cfg().sys.storage.keep_record = _keep_record
                    tp_cfg().sys.storage.cleanup_hour = _cleanup_hour
                    tp_cfg().sys.storage.cleanup_minute = _cleanup_minute
                else:
                    return self.write_json(err)

            if 'ldap' in args:
                processed = True
                _cfg = args['ldap']
                # _password = _cfg['password']
                _server = _cfg['server']
                _port = _cfg['port']
                _domain = _cfg['domain']
                _admin = _cfg['admin']
                _base_dn = _cfg['base_dn']
                _filter = _cfg['filter']
                _attr_username = _cfg['attr_username']
                _attr_surname = _cfg['attr_surname']
                _attr_email = _cfg['attr_email']

                if len(_cfg['password']) == 0:
                    _cfg['password'] = tp_cfg().sys_ldap_password

                if len(_cfg['password']) == 0:
                    return self.write_json(TPE_PARAM, '请设置LDAP管理员密码')

                # TODO: encrypt the password before save by core-service.

                err = system_model.save_config(self, '更新LDAP设置', 'ldap', _cfg)
                if err == TPE_OK:
                    tp_cfg().sys.ldap.server = _server
                    tp_cfg().sys.ldap.port = _port
                    tp_cfg().sys.ldap.domain = _domain
                    tp_cfg().sys.ldap.admin = _admin
                    tp_cfg().sys.ldap.base_dn = _base_dn
                    tp_cfg().sys.ldap.filter = _filter
                    tp_cfg().sys.ldap.attr_username = _attr_username
                    tp_cfg().sys.ldap.attr_surname = _attr_surname
                    tp_cfg().sys.ldap.attr_email = _attr_email
                    # 特殊处理，防止前端拿到密码
                    tp_cfg().sys_ldap_password = _cfg['password']
                else:
                    return self.write_json(err)

            if not processed:
                return self.write_json(TPE_PARAM)

            return self.write_json(TPE_OK)
        except:
            log.e('\n')
            self.write_json(TPE_FAILED)


class DoSendTestMailHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            _server = args['server']
            _port = int(args['port'])
            _ssl = args['ssl']
            _sender = args['sender']
            _password = args['password']
            _recipient = args['recipient']
        except:
            return self.write_json(TPE_PARAM)

        code, msg = yield mail.tp_send_mail(
            _recipient,
            '您好！\n\n这是一封测试邮件，仅用于验证系统的邮件发送模块工作是否正常。\n\n请忽略本邮件。',
            subject='测试邮件',
            sender='Teleport Server <{}>'.format(_sender),
            server=_server,
            port=_port,
            use_ssl=_ssl,
            username=_sender,
            password=_password
        )

        self.write_json(code, message=msg)


class DoLdapListUserAttrHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            cfg = args['ldap']
            cfg['port'] = int(cfg['port'])
            if len(cfg['password']) == 0:
                if len(tp_cfg().sys_ldap_password) == 0:
                    return self.write_json(TPE_PARAM, message='需要设置LDAP管理员密码')
                else:
                    cfg['password'] = tp_cfg().sys_ldap_password
        except:
            return self.write_json(TPE_PARAM)

        try:
            ldap = Ldap(cfg['server'], cfg['port'], cfg['base_dn'])
            ret, data, err_msg = ldap.get_all_attr(cfg['admin'], cfg['password'], cfg['filter'])
            if ret != TPE_OK:
                return self.write_json(ret, message=err_msg)
            else:
                return self.write_json(ret, data=data)
        except:
            log.e('')
            return self.write_json(TPE_PARAM)


class DoLdapConfigTestHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            cfg = args['ldap']
            cfg['port'] = int(cfg['port'])
            if len(cfg['password']) == 0:
                if len(tp_cfg().sys_ldap_password) == 0:
                    return self.write_json(TPE_PARAM, message='需要设置LDAP管理员密码')
                else:
                    cfg['password'] = tp_cfg().sys_ldap_password
        except:
            return self.write_json(TPE_PARAM)

        try:
            ldap = Ldap(cfg['server'], cfg['port'], cfg['base_dn'])
            ret, data, err_msg = ldap.list_users(
                cfg['admin'], cfg['password'], cfg['filter'],
                cfg['attr_username'], cfg['attr_surname'], cfg['attr_email'],
                size_limit=10
            )

            if ret != TPE_OK:
                return self.write_json(ret, message=err_msg)
            else:
                return self.write_json(ret, data=data)
        except:
            log.e('')
            return self.write_json(TPE_PARAM)


class DoLdapGetUsersHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            if len(tp_cfg().sys_ldap_password) == 0:
                return self.write_json(TPE_PARAM, message='LDAP未能正确配置，需要管理员密码')
            else:
                _password = tp_cfg().sys_ldap_password
            _server = tp_cfg().sys.ldap.server
            _port = tp_cfg().sys.ldap.port
            _admin = tp_cfg().sys.ldap.admin
            _base_dn = tp_cfg().sys.ldap.base_dn
            _filter = tp_cfg().sys.ldap.filter
            _attr_username = tp_cfg().sys.ldap.attr_username
            _attr_surname = tp_cfg().sys.ldap.attr_surname
            _attr_email = tp_cfg().sys.ldap.attr_email
        except:
            return self.write_json(TPE_PARAM)

        try:
            ldap = Ldap(_server, _port, _base_dn)
            ret, data, err_msg = ldap.list_users(_admin, _password, _filter, _attr_username, _attr_surname, _attr_email)
            if ret != TPE_OK:
                return self.write_json(ret, message=err_msg)

            exits_users = user.get_users_by_type(TP_USER_TYPE_LDAP)
            bound_users = []
            for u in exits_users:
                h = hashlib.sha1()
                h.update(u['ldap_dn'].encode())
                bound_users.append(h.hexdigest())

            ret_data = []
            for u in data:
                h = hashlib.sha1()
                h.update(u.encode())
                _id = h.hexdigest()
                if _id in bound_users:
                    continue

                _user = data[u]
                _user['id'] = h.hexdigest()
                ret_data.append(_user)
            return self.write_json(ret, data=ret_data)
        except:
            log.e('')
            return self.write_json(TPE_PARAM)


class DoLdapImportHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            dn_hash_list = args['ldap_users']

            if len(tp_cfg().sys_ldap_password) == 0:
                return self.write_json(TPE_PARAM, message='LDAP未能正确配置，需要管理员密码')
            else:
                _password = tp_cfg().sys_ldap_password
            _server = tp_cfg().sys.ldap.server
            _port = tp_cfg().sys.ldap.port
            _admin = tp_cfg().sys.ldap.admin
            _base_dn = tp_cfg().sys.ldap.base_dn
            _filter = tp_cfg().sys.ldap.filter
            _attr_username = tp_cfg().sys.ldap.attr_username
            _attr_surname = tp_cfg().sys.ldap.attr_surname
            _attr_email = tp_cfg().sys.ldap.attr_email
        except:
            return self.write_json(TPE_PARAM)

        try:
            ldap = Ldap(_server, _port, _base_dn)
            ret, data, err_msg = ldap.list_users(_admin, _password, _filter, _attr_username, _attr_surname, _attr_email)

            if ret != TPE_OK:
                return self.write_json(ret, message=err_msg)

            need_import = []
            for u in data:
                h = hashlib.sha1()
                h.update(u.encode())

                dn_hash = h.hexdigest()
                for x in dn_hash_list:
                    if x == dn_hash:
                        _user = data[u]
                        _user['dn'] = u
                        need_import.append(_user)
                        break

            if len(need_import) == 0:
                return self.write_json(ret, message='没有可以导入的LDAP用户')

            return self._do_import(need_import)
        except:
            log.e('')
            return self.write_json(TPE_PARAM)

    def _do_import(self, users):
        success = list()
        failed = list()
        try:
            user_list = []
            for _u in users:
                if 'surname' not in _u:
                    _u['surname'] = _u['username']
                if 'email' not in _u:
                    _u['email'] = ''

                u = dict()
                u['_line'] = 0
                u['_id'] = 0
                u['type'] = TP_USER_TYPE_LDAP
                u['ldap_dn'] = _u['dn']
                u['username'] = '{}@{}'.format(_u['username'], tp_cfg().sys.ldap.domain)
                u['surname'] = _u['surname']
                u['email'] = _u['email']
                u['mobile'] = ''
                u['qq'] = ''
                u['wechat'] = ''
                u['desc'] = ''
                u['password'] = ''

                # fix
                if len(u['surname']) == 0:
                    u['surname'] = u['username']
                u['username'] = u['username'].lower()

                user_list.append(u)

            print(user_list)
            user.create_users(self, user_list, success, failed)

            # 对于创建成功的用户，发送密码邮件函
            sys_smtp_password = tp_cfg().sys_smtp_password
            if len(sys_smtp_password) > 0:
                web_url = '{}://{}'.format(self.request.protocol, self.request.host)
                for u in user_list:
                    if u['_id'] == 0 or len(u['email']) == 0:
                        continue
                    u['email'] = 'apex.liu@qq.com'

                    mail_body = '{surname} 您好！\n\n已为您创建teleport系统用户账号，现在可以使用以下信息登录teleport系统：\n\n' \
                                '登录用户名：{username}\n' \
                                '密码：您正在使用的域登录密码\n' \
                                '地址：{web_url}\n\n\n\n' \
                                '[本邮件由teleport系统自动发出，请勿回复]' \
                                '\n\n' \
                                ''.format(surname=u['surname'], username=u['username'], web_url=web_url)

                    err, msg = yield mail.tp_send_mail(u['email'], mail_body, subject='用户密码函')
                    if err != TPE_OK:
                        failed.append({'line': u['_line'], 'error': '无法发送密码函到邮箱 {}，错误：{}。'.format(u['email'], msg)})

            # 统计结果
            total_success = 0
            total_failed = 0
            for u in user_list:
                if u['_id'] == 0:
                    total_failed += 1
                else:
                    total_success += 1

            # 生成最终结果信息
            if len(failed) == 0:
                # ret['code'] = TPE_OK
                # ret['message'] = '共导入 {} 个用户账号！'.format(total_success)
                return self.write_json(TPE_OK, message='共导入 {} 个用户账号！'.format(total_success))
            else:
                # ret['code'] = TPE_FAILED
                msg = ''
                if total_success > 0:
                    msg = '{} 个用户账号导入成功，'.format(total_success)
                if total_failed > 0:
                    msg += '{} 个用户账号未能导入！'.format(total_failed)

                # ret['data'] = failed
                return self.write_json(TPE_FAILED, data=failed, message=msg)

        except:
            log.e('got exception when import LDAP user.\n')
            # ret['code'] = TPE_FAILED
            msg = ''
            if len(success) > 0:
                msg += '{} 个用户账号导入后发生异常！'.format(len(success))
            else:
                msg = '发生异常！'

            # ret['data'] = failed
            return self.write_json(TPE_FAILED, data=failed, message=msg)


class DoCleanupStorageHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        code, msg = yield record.cleanup_storage(self)

        self.write_json(code, data=msg)


class DoRebuildOpsAuzMapHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return

        err = audit.build_auz_map()
        self.write_json(err)


class DoRebuildAuditAuzMapHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        err = ops.build_auz_map()
        self.write_json(err)
