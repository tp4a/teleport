# -*- coding: utf-8 -*-

import json

from eom_app.module import user
from eom_common.eomcore.logger import *
from .base import TPBaseHandler, TPBaseUserAuthHandler, TPBaseJsonHandler, TPBaseUserAuthJsonHandler
from eom_app.app.util import gen_captcha


class LoginHandler(TPBaseHandler):
    def get(self):
        _user = self.get_current_user()
        if _user['id'] == 0:
            user_name = ''
        else:
            user_name = _user['name']

        param = {
            'ref': self.get_argument('ref', '/'),
            'user_name': user_name
        }
        self.render('auth/login.mako', page_param=json.dumps(param))


class VerifyUser(TPBaseJsonHandler):
    def post(self):
        code = self.get_session('captcha')
        if code is None:
            self.write_json(-1, 'can not get captcha')
            return

        self.del_session('captcha')

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            captcha = args['captcha']
            username = args['username']
            userpwd = args['userpwd']
        else:
            self.write_json(-1, 'invalid param')
            return

        if code.lower() != captcha.lower():
            self.write_json(-1, 'invalid captcha')
            return

        try:
            user_id, account_type, nickname = user.verify_user(username, userpwd)
            if user_id == 0:
                self.write_json(-1, 'no such user or password.')
                return

            _user = self.get_session('user')
            if _user is None:
                _user = dict()
                _user['id'] = 0
                _user['name'] = 'guest'
                _user['nick_name'] = '访客'
                _user['status'] = 0
                _user['phone_num'] = '110'
                _user['type'] = 0
                _user['permission'] = 0
                _user['is_login'] = False

            _user['id'] = user_id
            _user['is_login'] = True
            _user['name'] = username
            _user['nick_name'] = nickname
            _user['type'] = account_type

            self.set_session('user', _user)
            return self.write_json(0)

        except:
            log.e('can not set session.')
            self.write_json(-1, 'session error.')


class LogoutHandler(TPBaseUserAuthHandler):
    def get(self):
        _user = self.get_current_user()
        _user['is_login'] = False
        self.set_session('user', _user)

        self.redirect('/auth/login')


class GetCaptchaHandler(TPBaseHandler):
    def get(self):
        code, img_data = gen_captcha()
        self.set_session('captcha', code)
        self.set_header('Content-Type', 'image/jpeg')
        self.write(img_data)


class VerifyCaptchaHandler(TPBaseJsonHandler):
    def post(self):
        code = self.get_session('captcha')
        if code is None:
            self.write_json(-1)
            return

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            captcha = args['captcha']
        else:
            self.write_json(-1)
            return

        if code.lower() != captcha.lower():
            self.write_json(-1)
            return

        self.write_json(0)


class ModifyPwd(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return
        _old_pwd = args['o_pwd']
        _new_pwd = args['n_pwd']

        if _old_pwd is None or _new_pwd is None:
            self.write_json(-1)
            return

        user_info = self.get_current_user()
        try:
            ret = user.modify_pwd(_old_pwd, _new_pwd, user_info['id'])
            self.write_json(0, ret)
        except:
            self.write_json(-1)
