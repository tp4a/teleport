# -*- coding: utf-8 -*-

import datetime
import json
import shutil

import app.model.system as system_model
import tornado.gen
from app.base import mail
from app.base.configs import get_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.logger import *
from app.const import *
from app.model import syslog


# time_now = int(time.time())
class DoGetTimeHandler(TPBaseJsonHandler):
    def post(self):
        time_now = int(datetime.datetime.utcnow().timestamp())
        self.write_json(TPE_OK, data=time_now)


class ConfigHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        if not get_cfg().core.detected:
            total_size = 0
            free_size = 0
        else:
            # total_size, free_size = get_free_space_bytes(get_cfg().core.replay_path)
            total_size, _, free_size = shutil.disk_usage(get_cfg().core.replay_path)

        param = {
            'total_size': total_size,
            'free_size': free_size,
            'core_cfg': get_cfg().core,
            'sys_cfg': get_cfg().sys
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
            err, role_id = system_model.add_role(self, role_id, role_name, privilege)
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
            _server = args['smtp_server']
            _port = int(args['smtp_port'])
            _ssl = args['smtp_ssl']
            _sender = args['smtp_sender']
            _password = args['smtp_password']
            _recipient = args['smtp_recipient']
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


class DoSaveMailConfigHandler(TPBaseJsonHandler):
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
            _server = args['smtp_server']
            _port = int(args['smtp_port'])
            _ssl = args['smtp_ssl']
            _sender = args['smtp_sender']
            _password = args['smtp_password']
        except:
            return self.write_json(TPE_PARAM)

        # 调用Model模块来操作数据库
        code, msg = system_model.save_mail_config(_server, _port, _ssl, _sender, _password)
        if code == TPE_OK:
            # 同时更新内存缓存
            get_cfg().sys.smtp.server = _server
            get_cfg().sys.smtp.port = _port
            get_cfg().sys.smtp.ssl = _ssl
            get_cfg().sys.smtp.sender = _sender
            get_cfg().sys_smtp_password = _password

        self.write_json(code, message=msg)
