# -*- coding: utf-8 -*-

import json

from eom_app.app.const import *
from eom_app.app.configs import app_cfg
from eom_app.module import user
from eom_common.eomcore.logger import *
from .base import TPBaseHandler, TPBaseUserAuthHandler, TPBaseJsonHandler, TPBaseUserAuthJsonHandler
from eom_app.app.util import gen_captcha

cfg = app_cfg()


class LoginHandler(TPBaseHandler):
    def get(self):
        _user = self.get_current_user()
        _ref = self.get_argument('ref', '/')

        if _user['is_login']:
            self.redirect(_ref)
            return

        if _user['id'] == 0:
            user_name = ''
        else:
            user_name = _user['name']

        param = {
            'ref': _ref,
            'user_name': user_name
        }
        self.render('auth/login.mako', page_param=json.dumps(param))


class VerifyUser(TPBaseJsonHandler):
    def post(self):
        code = self.get_session('captcha')
        if code is None:
            self.write_json(-1, '验证码已失效')
            return

        self.del_session('captcha')

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            captcha = args['captcha']
            username = args['username']
            userpwd = args['userpwd']
            remember = args['remember']
        else:
            self.write_json(-1, '系统内部错误')
            return

        if code.lower() != captcha.lower():
            self.write_json(-1, '验证码错误')
            return

        try:
            user_id, account_type, nickname = user.verify_user(username, userpwd)
            if user_id == 0:
                if cfg.app_mode == APP_MODE_MAINTENANCE:
                    self.write_json(-2, '系统维护中，请稍候再试')
                else:
                    self.write_json(-1, '用户名/密码错误')
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

            if remember:
                self.set_session('user', _user, 12*60*60)
            else:
                self.set_session('user', _user)
            return self.write_json(0)

        except:
            log.e('can not set session.')
            self.write_json(-1, '无法记录用户登录状态')


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
