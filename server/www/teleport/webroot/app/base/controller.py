# -*- coding: utf-8 -*-

import binascii
import json
import os
import time
from urllib.parse import quote

import mako.lookup
import mako.template
import tornado.web
from app.base.logger import log
from app.base.session import tp_session
from app.const import *
from tornado.escape import json_encode


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
        self._user = None

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
            log.w('request `{}`, should be web page request.\n'.format(self.request.uri))
            self.write_json(-1, 'should be web page request.')
            return
        self.finish(self.render_string(template_path, **kwargs))

    def write_json(self, code, message='', data=None):
        if self._mode != self.MODE_JSON:
            log.w('request `{}`, should be json request.\n'.format(self.request.uri))
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

        _user = self.get_session('user')
        if _user is None:
            _user = {
                'id': 0,
                'username': 'guest',
                'surname': '访客',
                'role_id': 0,
                'role': '访客',
                'privilege': TP_PRIVILEGE_NONE,
                '_is_login': False
            }
        self._user = _user

    def set_session(self, name, value, expire=None):
        k = '{}-{}'.format(name, self._s_id)
        tp_session().set(k, value, expire)

    def get_session(self, name, _default=None):
        k = '{}-{}'.format(name, self._s_id)
        return tp_session().get(k, _default)

    def del_session(self, name):
        k = '{}-{}'.format(name, self._s_id)
        return tp_session().set(k, '', -1)

    def get_current_user(self):
        return self._user

    def check_privilege(self, require_privilege, need_process=True):
        if not self._user['_is_login']:
            if self._mode == self.MODE_HTTP:
                if need_process:
                    self.redirect('/auth/login?ref={}'.format(quote(self.request.uri)))
            elif self._mode == self.MODE_JSON:
                if need_process:
                    self.write_json(TPE_NEED_LOGIN)
            else:
                if need_process:
                    raise RuntimeError("invalid request mode.")
                else:
                    return TPE_HTTP_METHOD
            return TPE_NEED_LOGIN

        else:
            if (self._user['privilege'] & require_privilege) != 0:
                return TPE_OK

        if self._mode == self.MODE_HTTP:
            if need_process:
                self.show_error_page(TPE_PRIVILEGE)
        elif self._mode == self.MODE_JSON:
            if need_process:
                self.write_json(TPE_PRIVILEGE)
        else:
            if need_process:
                raise RuntimeError("invalid request mode.")
            else:
                return TPE_HTTP_METHOD

        return TPE_PRIVILEGE

    def show_error_page(self, err_code):
        self.render('error/error.mako', page_param=json.dumps({'err_code': err_code}))


class TPBaseJsonHandler(TPBaseHandler):
    """
    所有返回JSON数据的控制器均从本类继承，返回的数据格式一律包含三个字段：code/msg/data
    code: TPE_OK=成功，其他=失败
    msg: 字符串，一般用于code为非零时，指出错误原因
    data: 一般用于成功操作的返回的业务数据
    """

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self._mode = self.MODE_JSON
