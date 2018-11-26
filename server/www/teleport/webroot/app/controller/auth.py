# -*- coding: utf-8 -*-

import json
from urllib.parse import quote

from app.base.configs import tp_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.const import *
from app.logic.auth.captcha import tp_captcha_generate_image
from app.model import syslog
from app.model import user


class LoginHandler(TPBaseHandler):
    def get(self):
        from app.base.db import get_db
        if tp_cfg().app_mode == APP_MODE_MAINTENANCE and get_db().need_create:
            _user = {
                'id': 0,
                'username': 'installer',
                'surname': '安装程序',
                'role_id': 0,
                'role': '',
                'privilege': TP_PRIVILEGE_SYS_CONFIG,
                '_is_login': True
            }
            self.set_session('user', _user)
            self.redirect('/maintenance/install')
            return

        _user = self.get_current_user()
        _ref = quote(self.get_argument('ref', '/'))

        if _user['_is_login']:
            self.redirect(_ref)
            return

        if _user['id'] == 0:
            username = self.get_cookie('username')
            if username is None:
                username = ''
        else:
            username = _user['username']

        default_auth_type = tp_cfg().sys.login.auth
        param = {
            'ref': _ref,
            'username': username,
            'default_auth': default_auth_type
        }
        self.render('auth/login.mako', page_param=json.dumps(param))


class DoLoginHandler(TPBaseJsonHandler):
    def post(self):
        sys_cfg = tp_cfg().sys

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)

        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT, '参数错误')

        try:
            login_type = args['type']
            captcha = args['captcha'].strip()
            username = args['username'].strip().lower()
            password = args['password']
            oath = args['oath'].strip()
            remember = args['remember']
        except:
            return self.write_json(TPE_PARAM)

        if login_type not in [TP_LOGIN_AUTH_USERNAME_PASSWORD,
                              TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA,
                              TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH,
                              TP_LOGIN_AUTH_USERNAME_OATH
                              ]:
            return self.write_json(TPE_PARAM, '未知的认证方式')

        if login_type == TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA:
            oath = None
            code = self.get_session('captcha')
            if code is None:
                return self.write_json(TPE_CAPTCHA_EXPIRED, '验证码已失效')
            if code.lower() != captcha.lower():
                return self.write_json(TPE_CAPTCHA_MISMATCH, '验证码错误')
        elif login_type in [TP_LOGIN_AUTH_USERNAME_OATH, TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH]:
            if len(oath) == 0:
                return self.write_json(TPE_OATH_MISMATCH, '未提供身份验证器动态验证码')

        self.del_session('captcha')

        if len(username) == 0:
            return self.write_json(TPE_PARAM, '未提供登录用户名')

        if login_type not in [TP_LOGIN_AUTH_USERNAME_PASSWORD,
                              TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA,
                              TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH
                              ]:
            password = None
        if login_type not in [TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH,
                              TP_LOGIN_AUTH_USERNAME_OATH
                              ]:
            oath = None

        # 检查用户名合法性，防止SQL注入攻击
        if '<' in username or '>' in username:
            username = username.replace('<', '&lt;')
            username = username.replace('>', '&gt;')
            err = TPE_USER_AUTH
            syslog.sys_log({'username': '???', 'surname': '???'}, self.request.remote_ip, TPE_NOT_EXISTS, '登录失败，可能是攻击行为。试图使用用户名 {} 进行登录。'.format(username))
            return self.write_json(err)

        err, user_info = user.login(self, username, password=password, oath_code=oath)
        if err != TPE_OK:
            if err == TPE_NOT_EXISTS:
                err = TPE_USER_AUTH
                syslog.sys_log({'username': '???', 'surname': '???'}, self.request.remote_ip, TPE_NOT_EXISTS, '登录失败，用户`{}`不存在'.format(username))
            return self.write_json(err)

        # 判断此用户是否被允许使用当前登录认证方式
        auth_type = user_info.auth_type
        if auth_type == 0:
            auth_type = sys_cfg.login.auth

        if (auth_type & login_type) != login_type:
            return self.write_json(TPE_USER_AUTH, '不允许使用此身份认证方式')

        self._user = user_info
        self._user['_is_login'] = True
        # del self._user['password']
        # del self._user['oath_secret']

        if remember:
            self.set_session('user', self._user, 12 * 60 * 60)
        else:
            self.set_session('user', self._user)

        user.update_login_info(self, user_info['id'])

        # 记录登录日志
        syslog.sys_log(self._user, self.request.remote_ip, TPE_OK, "登录成功")

        self.set_cookie('username', username)

        return self.write_json(TPE_OK)


class LogoutHandler(TPBaseHandler):
    def get(self):
        self._user['_is_login'] = False
        self.set_session('user', self._user)

        self.redirect('/auth/login')


class DoLogoutHandler(TPBaseJsonHandler):
    def post(self):
        self._user['_is_login'] = False
        self.set_session('user', self._user)
        return self.write_json(TPE_OK)


class CaptchaHandler(TPBaseHandler):
    def get(self):
        h = int(self.get_argument('h', 36))
        code, img_data = tp_captcha_generate_image(h)
        self.set_session('captcha', code, expire=10 * 60)  # 验证码有效期为10分钟
        self.set_header('Content-Type', 'image/jpeg')
        self.write(img_data)


class VerifyCaptchaHandler(TPBaseJsonHandler):
    def post(self):
        code = self.get_session('captcha')
        if code is None:
            return self.write_json(TPE_CAPTCHA_EXPIRED)

        args = self.get_argument('args', None)
        if args is not None:
            try:
                args = json.loads(args)
            except:
                return self.write_json(TPE_JSON_FORMAT)
            try:
                captcha = args['captcha']
            except:
                return self.write_json(TPE_PARAM)
        else:
            return self.write_json(TPE_PARAM)

        if code.lower() != captcha.lower():
            return self.write_json(TPE_CAPTCHA_MISMATCH, '验证码错误')

        return self.write_json(TPE_OK)

# class ModifyPwd(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#         _old_pwd = args['o_pwd']
#         _new_pwd = args['n_pwd']
#
#         if _old_pwd is None or _new_pwd is None:
#             return self.write_json(-2, '参数错误')
#
#         user_info = self.get_current_user()
#         try:
#             ret = user.modify_pwd(_old_pwd, _new_pwd, user_info['id'])
#             if 0 == ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(ret)
#         except:
#             log.e('modify password failed.')
#             return self.write_json(-4, '发生异常')
#
#
