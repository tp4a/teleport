# -*- coding: utf-8 -*-

import json

from eom_app.module import user
from eom_common.eomcore.logger import *
from .base import SwxAppHandler, SwxJsonpHandler, SwxAuthJsonHandler
from eom_app.app.util import gen_captcha


class LoginHandler(SwxAppHandler):
    def get(self):
        _user = self.get_current_user()
        if _user['id'] == 0:
            user_name = ''
        else:
            user_name = _user['name']

        page_param = {
            'ref': self.get_argument('ref', '/'),
            'login_type': 'account',
            'user_name': user_name
        }
        page_param = json.dumps(page_param)
        self.render('auth/login.mako', page_param=page_param)


class VerifyUser(SwxJsonpHandler):
    def get(self):
        code = self.get_session('captcha')
        if code is None:
            self.write_jsonp(-1)
            return

        captcha = self.get_argument('captcha', None)
        username = self.get_argument('username', None)
        userpwd = self.get_argument('userpwd', None)

        if captcha is None or username is None:
            self.write_jsonp(-1)
            return
        if code.lower() != captcha.lower():
            self.write_jsonp(-1)
            return

        self.del_session('captcha')

        try:
            user_id, account_type, nickname = user.verify_user(username, userpwd)
            if user_id == 0:
                self.write_jsonp(-1)
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
            # log.v('set session ok.\n')
            return self.write_jsonp(0)

        except:
            log.e('can not set session.')
            self.write_jsonp(-1)


class LogoutHandler(SwxAppHandler):
    def get(self):
        _user = self.get_current_user()
        _user['is_login'] = False
        self.set_session('user', _user)

        self.redirect('/auth/login')


class GetCaptchaHandler(SwxAppHandler):
    def get(self):
        code, img_data = gen_captcha()
        self.set_session('captcha', code)
        self.set_header('Content-Type', 'image/jpeg')
        self.write(img_data)


class VerifyCaptchaHandler(SwxJsonpHandler):
    def get(self):
        code = self.get_session('captcha')
        if code is None:
            self.write_jsonp(-1)
            return

        captcha = self.get_argument('captcha', None)
        if captcha is None:
            self.write_jsonp(-1)
            return

        if code.lower() != captcha.lower():
            self.write_jsonp(-1)
            return

        self.write_jsonp(0)


class ModifyPwd(SwxAuthJsonHandler):
    def post(self):
        # print('verify-ticket')

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
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
