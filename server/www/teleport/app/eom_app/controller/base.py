# -*- coding: utf-8 -*-

import binascii
import os
import time
from urllib.parse import quote

import mako.lookup
import mako.template
import tornado.web
from eom_app.app.configs import app_cfg
from eom_app.app.const import *
from eom_app.app.db import get_db
from eom_app.app.session import web_session, SESSION_EXPIRE
from tornado.escape import json_encode

cfg = app_cfg()


class TPBaseHandler(tornado.web.RequestHandler):
    """
    所有http请求处理的基类，只有极少数的请求如登录、维护直接从本类继承，其他的所有类均从本类的子类（控制权限的类）继承
    """

    MODE_HTTP = 0
    MODE_JSON = 1

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self._s_id = None
        self._mode = self.MODE_HTTP

    def initialize(self):
        template_path = self.get_template_path()
        self.lookup = mako.lookup.TemplateLookup(directories=[template_path], input_encoding='utf-8', output_encoding='utf-8')

    def render_string(self, template_name, **kwargs):
        template = self.lookup.get_template(template_name)
        namespace = self.get_template_namespace()
        namespace.update(kwargs)
        return template.render(**namespace)

    def render(self, template_path, **kwargs):
        if self._mode != self.MODE_HTTP:
            self.write_json(-1, 'should be web page request.')
            return
        self.finish(self.render_string(template_path, **kwargs))

    def write_json(self, code, message='', data=None):
        if self._mode != self.MODE_JSON:
            self.write('should be json request.')
            self.finish()
            return

        if not isinstance(code, int):
            raise RuntimeError('`code` must be a integer.')
        if not isinstance(message, str):
            raise RuntimeError('`msg` must be a string.')

        if data is None:
            data = list()

        _ret = {'code': code, 'message': message, 'data': data}

        self.set_header("Content-Type", "application/json")
        self.write(json_encode(_ret))
        self.finish()

    def write_raw_json(self, data=None):
        if self._mode != self.MODE_JSON:
            self.write('should be json request.')
            self.finish()
            return

        if data is None:
            data = list()

        self.set_header("Content-Type", "application/json")
        self.write(json_encode(data))
        self.finish()

    def prepare(self):
        super().prepare()
        if self._finished:
            return

        # if self.application.settings.get("xsrf_cookies"):
        #     x = self.xsrf_token

        self._s_id = self.get_cookie('_sid')
        if self._s_id is None:
            self._s_id = 'tp_{}_{}'.format(int(time.time()), binascii.b2a_hex(os.urandom(8)).decode())
            self.set_cookie('_sid', self._s_id)

    def set_session(self, name, value, expire=SESSION_EXPIRE):
        k = '{}-{}'.format(self._s_id, name)
        web_session().set(k, value, expire)

    def get_session(self, name, _default=None):
        k = '{}-{}'.format(self._s_id, name)
        return web_session().get(k, _default)

    def del_session(self, name):
        k = '{}-{}'.format(self._s_id, name)
        return web_session().set(k, '', -1)

    def get_current_user(self):
        user = self.get_session('user')
        if user is None:
            user = dict()
            user['id'] = 0
            user['name'] = 'guest'
            user['nick_name'] = '访客'
            user['status'] = 0
            user['phone_num'] = '110'
            user['type'] = 0
            user['permission'] = 0
            user['is_login'] = False

        return user


class TPBaseJsonHandler(TPBaseHandler):
    """
    所有返回JSON数据的控制器均从本类集成，返回的数据格式一律包含三个字段：code/msg/data
    code: 0=成功，其他=失败
    msg: 字符串，一般用于code为非零，指出错误原因
    data: 一般用于成功操作的返回的业务数据
    """

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self._mode = self.MODE_JSON


class TPBaseUserAuthHandler(TPBaseHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()
        if self._finished:
            return

        reference = self.request.uri

        user = self.get_current_user()
        if not user['is_login']:
            if reference != '/auth/login':
                x = quote(reference)
                self.redirect('/auth/login?ref={}'.format(x))
            else:
                self.redirect('/auth/login')
        else:
            if cfg.app_mode == APP_MODE_MAINTENANCE:
                if user['type'] != 100:
                    self.render('maintenance/index.mako')
                else:
                    if not reference.startswith('/maintenance/'):
                        if get_db().need_create:
                            self.redirect('/maintenance/install')
                        elif get_db().need_upgrade:
                            self.redirect('/maintenance/upgrade')


class TPBaseAdminAuthHandler(TPBaseHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()
        if self._finished:
            return

        reference = self.request.uri

        user = self.get_current_user()
        if not user['is_login'] or user['type'] != 100:
            if reference != '/auth/login':  # 防止循环重定向
                x = quote(reference)
                self.redirect('/auth/login?ref={}'.format(x))
            else:
                self.redirect('/auth/login')
        else:
            if cfg.app_mode == APP_MODE_MAINTENANCE:
                if not reference.startswith('/maintenance/'):
                    if get_db().need_create:
                        self.redirect('/maintenance/install')
                    elif get_db().need_upgrade:
                        self.redirect('/maintenance/upgrade')


class TPBaseUserAuthJsonHandler(TPBaseJsonHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()
        if self._finished:
            return

        reference = self.request.uri

        user = self.get_current_user()
        if not user['is_login']:
            if reference != '/auth/login':
                self.write_json(-99)
            else:
                self.write_json(-99)

        else:
            if cfg.app_mode == APP_MODE_MAINTENANCE and user['type'] != 100:
                self.write_json(-1, 'maintenance mode')
            else:
                pass


class TPBaseAdminAuthJsonHandler(TPBaseJsonHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()
        if self._finished:
            return

        reference = self.request.uri

        user = self.get_current_user()
        if not user['is_login'] or user['type'] != 100:
            if reference != '/auth/login':
                self.write_json(-99)
