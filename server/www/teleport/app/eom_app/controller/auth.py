# -*- coding: utf-8 -*-

import json
import random
from random import Random

from eom_app.module import user
from eom_common.eomcore.logger import *
from .base import SwxAppHandler, SwxJsonpHandler, SwxAuthJsonHandler
from .helper.captcha import gen_captcha


class LoginHandler(SwxAppHandler):
    def get(self):
        ref = self.get_argument('ref', '/')

        self.render('auth/login.mako', reference=ref, captcha_random=random.random())


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

        # log.v('try to set-session.\n')
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
        user = self.get_current_user()
        user['is_login'] = False
        self.set_session('user', user)

        # self.render('login/login.mako', captcha_random=random.random())
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


class VerifyTicketHandler(SwxJsonpHandler):
    def get(self):
        # print('verify-ticket')

        code = self.get_session('captcha')
        if code is None:
            self.write_jsonp(-1)
            return

        captcha = self.get_argument('captcha', None)
        username = self.get_argument('username', None)
        user_id = self.get_argument('user_id', None)
        ticket = self.get_argument('ticket', None)

        if captcha is None or username is None or ticket is None:
            self.write_jsonp(-1)
            return

        if code.lower() != captcha.lower():
            self.write_jsonp(-1)
            return

        self.del_session('captcha')

        # if not self.is_ticket_valid(username, ticket):
        #     self.write_jsonp(-1)
        #     return

        # log.v('try to set-session.\n')
        try:
            _user = user.get_user_by_id(user_id)
            if _user is None:
                self.write_jsonp(-1)
                return

            # _user = dict()
            # _user['id'] = user_id
            # # user['account'] = username # login-name
            # _user['name'] = username # real-name
            _user['is_login'] = True

            self.set_session('user', _user)
            # log.v('set session ok.\n')

            self.write_jsonp(0)
        except:
            log.e('can not set session.')
            self.write_jsonp(-1)


#
# class QuickLoginHandler(SwxJsonpHandler):
#     def get(self):
#         # code = self.get_session('captcha')
#         # if code is None:
#         #     self.write_jsonp(-1)
#         #     return
#
#         # captcha = self.get_argument('captcha', None)
#         # username = self.get_argument('username', None)
#         user_id = self.get_argument('uid', None)
#         ticket = self.get_argument('ticket', None)
#
#         # if captcha is None or username is None or ticket is None:
#         #     self.write_jsonp(-1)
#         #     return
#         #
#         # if code.lower() != captcha.lower():
#         #     self.write_jsonp(-1)
#         #     return
#
#         # self.del_session('captcha')
#
#         if not self.is_ticket_valid(ticket):
#             self.write_jsonp(-1)
#             return
#
#         _user = user.get_user_by_id(user_id)
#         if _user is None:
#             self.write_jsonp(-1)
#             return
#
#         # _user = dict()
#         # _user['id'] = user_id
#         # # user['account'] = username # login-name
#         # _user['name'] = username # real-name
#         _user['is_login'] = True
#
#         log.v('quick login ok, try to set session.\n')
#         try:
#             self.set_session('user', _user)
#             log.v('set session ok.\n')
#             self.write_jsonp(0)
#         except:
#             log.v('set session failed.\n')
#             self.write_jsonp(1)


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
            code = dict()
            code['code'] = ret
            self.write_json(0, data=code)
        except:
            log.e('can not set session.')
            self.write_json(-1)


#
# class GetEncData(SwxAuthJsonHandler):
#     def post(self):
#         # print('verify-ticket')
#
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#             # print('args', args)
#         else:
#             # ret = {'code':-1}
#             self.write_json(-1)
#             return
#         _pwd = args['pwd']
#
#         if _pwd is None:
#             self.write_json(-1)
#             return
#
#         try:
#             ret, data = user.get_enc_data_helper(_pwd)
#             code = dict()
#             code['code'] = ret
#             code['data'] = data
#             self.write_json(0, data=code)
#         except:
#             log.e('can not set session.')
#             self.write_json(-1)


# def random_str(randomlength=8):
#     _str = ''
#     chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
#     length = len(chars) - 1
#     _random = Random()
#     for i in range(randomlength):
#         _str += chars[_random.randint(0, length)]
#     return _str
