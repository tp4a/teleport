# -*- coding: utf-8 -*-

import binascii
import os
import time
from urllib.parse import quote

import mako.lookup
import mako.template
import tornado.web
from tornado.escape import json_encode

from eom_app.app.session import swx_session


class SwxBaseHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self._s_id = None
        self._s_val = dict()

    def initialize(self):
        template_path = self.get_template_path()
        self.lookup = mako.lookup.TemplateLookup(directories=[template_path], input_encoding='utf-8', output_encoding='utf-8')

    def render_string(self, template_name, **kwargs):
        template = self.lookup.get_template(template_name)
        namespace = self.get_template_namespace()
        namespace.update(kwargs)
        return template.render(**namespace)

    def render(self, template_path, **kwargs):
        self.finish(self.render_string(template_path, **kwargs))

    def prepare(self):

        if self.application.settings.get("xsrf_cookies"):
            x = self.xsrf_token

        self._s_id = self.get_cookie('_sid')
        if self._s_id is None:
            self._s_id = 'ywl_{}_{}'.format(int(time.time()), binascii.b2a_hex(os.urandom(8)).decode())
            self.set_cookie('_sid', self._s_id)
            swx_session().add(self._s_id, self._s_val)
        else:
            # print('sid:', self._s_id)
            self._s_val = swx_session().get(self._s_id)
            if self._s_val is None:
                self._s_val = dict()
                swx_session().add(self._s_id, self._s_val)

    def set_session(self, name, value):
        self._s_val[name] = value
        swx_session().set(self._s_id, self._s_val)

    def get_session(self, name, default=None):
        if name in self._s_val:
            return self._s_val[name]
        else:
            return default

    def del_session(self, name):
        if name in self._s_val:
            del self._s_val[name]

    def get_current_user(self):
        # return self.get_secure_cookie('user')
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


class SwxJsonpHandler(SwxBaseHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self._js_callback = ''

    def prepare(self):
        super().prepare()

        self._js_callback = self.get_argument('callback', None)
        if self._js_callback is None:
            raise RuntimeError('no callback in URL param.')

    def write_jsonp(self, err_code, data=None):

        self.write(self._js_callback)
        self.write('({code:')
        self.write('{}'.format(err_code))

        if data is None:
            self.write('})')
            return

        if not isinstance(data, dict):
            raise RuntimeError('jsonp data should be dict.')

        self.write(',data:')
        self.write(json_encode(data))
        self.write('})')


class SwxJsonHandler(SwxBaseHandler):
    """
    所有返回JSON数据的控制器均从本类集成，返回的数据格式一律包含三个字段：code/msg/data
    code: 0=成功，其他=失败
    msg: 字符串，一般用于code为非零是，指出错误原因
    data: 一般用于成功操作的返回的业务数据
    """
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def write_json(self, code, message='', data=None):
        if not isinstance(code, int):
            raise RuntimeError('`code` must be a integer.')
        if not isinstance(message, str):
            raise RuntimeError('`msg` must be a string.')

        if data is None:
            data = list()

        _ret = {'code':code, 'message':message, 'data':data}

        self.set_header("Content-Type", "application/json")
        self.write(json_encode(_ret))

    def write_raw_json(self, data=None):

        if data is None:
            data = list()

        self.set_header("Content-Type", "application/json")
        self.write(json_encode(data))


class SwxAuthHandler(SwxBaseHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()

        reference = self.request.uri

        user = self.get_current_user()
        if not user['is_login']:
            if reference != '/auth/login':
                x = quote(reference)
                self.redirect('/auth/login?ref={}'.format(x))
            else:
                self.redirect('/auth/login')


class SwxAdminHandler(SwxBaseHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()

        reference = self.request.uri

        user = self.get_current_user()
        if user['type'] != 100:
            if reference != '/auth/login':
                x = quote(reference)
                self.redirect('/auth/login?ref={}'.format(x))
            else:
                self.redirect('/auth/login')


class SwxAuthJsonpHandler(SwxBaseHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)


class SwxAuthJsonHandler(SwxJsonHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()

        reference = self.request.uri

        user = self.get_current_user()
        if not user['is_login']:
            if reference != '/auth/login':
                x = quote(reference)
                self.redirect('/auth/login?ref={}'.format(x))
            else:
                self.redirect('/auth/login')


class SwxAdminJsonHandler(SwxJsonHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def prepare(self):
        super().prepare()

        reference = self.request.uri

        user = self.get_current_user()
        if user['type'] != 100:
            if reference != '/auth/login':
                self.write_json(-99)
