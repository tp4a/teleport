# -*- coding: utf-8 -*-

import json

from app.base.configs import get_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.utils import tp_timestamp_utc_now
from app.const import *
from app.logic.auth.captcha import tp_captcha_generate_image
from app.logic.auth.oath import tp_oath_verify_code
from app.logic.auth.password import tp_password_verify
from app.model import syslog
from app.model import user


class LoginHandler(TPBaseHandler):
    def get(self):
        from app.base.db import get_db
        if get_cfg().app_mode == APP_MODE_MAINTENANCE and get_db().need_create:
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
        _ref = self.get_argument('ref', '/')

        if _user['_is_login']:
            self.redirect(_ref)
            return

        if _user['id'] == 0:
            username = self.get_cookie('username')
            if username is None:
                username = ''
        else:
            username = _user['username']

        param = {
            'ref': _ref,
            'username': username
        }
        self.render('auth/login.mako', page_param=json.dumps(param))


class DoLoginHandler(TPBaseJsonHandler):
    def post(self):
        sys_cfg = get_cfg().sys

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

        err, user_info = user.login(self, username, password=password, oath_code=oath)
        if err != TPE_OK:
            if err == TPE_NOT_EXISTS:
                err = TPE_USER_AUTH
                syslog.sys_log({'username': username, 'surname': username}, self.request.remote_ip, TPE_NOT_EXISTS, '登录失败，用户`{}`不存在'.format(username))
            return self.write_json(err)

        # err, user_info = user.get_by_username(username)
        # if err != TPE_OK:
        #     if err == TPE_NOT_EXISTS:
        #         syslog.sys_log({'username': username, 'surname': username}, self.request.remote_ip, TPE_NOT_EXISTS, '登录失败，用户`{}`不存在'.format(username))
        #     return self.write_json(err)
        #
        # if user_info.privilege == 0:
        #     # 尚未为此用户设置角色
        #     return self.write_json(TPE_PRIVILEGE, '用户尚未分配角色')
        #
        # if user_info['state'] == TP_STATE_LOCKED:
        #     # 用户已经被锁定，如果系统配置为一定时间后自动解锁，则更新一下用户信息
        #     if sys_cfg.login.lock_timeout != 0:
        #         if tp_timestamp_utc_now() - user_info.lock_time > sys_cfg.login.lock_timeout * 60:
        #             user_info.fail_count = 0
        #             user_info.state = TP_STATE_NORMAL
        #     if user_info['state'] == TP_STATE_LOCKED:
        #         syslog.sys_log(user_info, self.request.remote_ip, TPE_USER_LOCKED, '登录失败，用户已被锁定')
        #         return self.write_json(TPE_USER_LOCKED)
        # elif user_info['state'] == TP_STATE_DISABLED:
        #     syslog.sys_log(user_info, self.request.remote_ip, TPE_USER_DISABLED, '登录失败，用户已被禁用')
        #     return self.write_json(TPE_USER_DISABLED)
        # elif user_info['state'] != TP_STATE_NORMAL:
        #     syslog.sys_log(user_info, self.request.remote_ip, TPE_FAILED, '登录失败，系统内部错误')
        #     return self.write_json(TPE_FAILED)
        #
        # err_msg = ''
        # if login_type in [TP_LOGIN_AUTH_USERNAME_PASSWORD, TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA, TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH]:
        #     # 如果系统配置了密码有效期，则检查用户的密码是否失效
        #     if sys_cfg.password.timeout != 0:
        #         pass
        #
        #     if not tp_password_verify(password, user_info['password']):
        #         err, is_locked = user.update_fail_count(self, user_info)
        #         if is_locked:
        #             err_msg = '用户被临时锁定！'
        #         syslog.sys_log(user_info, self.request.remote_ip, TPE_USER_AUTH, '登录失败，密码错误！{}'.format(err_msg))
        #         return self.write_json(TPE_USER_AUTH)
        #
        # if login_type in [TP_LOGIN_AUTH_USERNAME_OATH, TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH]:
        #     # use oath
        #     if not tp_oath_verify_code(user_info['oath_secret'], oath):
        #         err, is_locked = user.update_fail_count(self, user_info)
        #         if is_locked:
        #             err_msg = '用户被临时锁定！'
        #         syslog.sys_log(user_info, self.request.remote_ip, TPE_OATH_MISMATCH, "登录失败，身份验证器动态验证码错误！{}".format(err_msg))
        #         return self.write_json(TPE_OATH_MISMATCH)

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
# class OathVerifyHandler(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             try:
#                 args = json.loads(args)
#                 code = args['code']
#             except:
#                 return self.write_json(-2, '参数错误')
#         else:
#             return self.write_json(-1, '参数错误')
#
#         # secret = self.get_session('tmp_oath_secret', None)
#         # if secret is None:
#         #     return self.write_json(-1, '内部错误！')
#         # self.del_session('tmp_oath_secret')
#
#         user_info = self.get_current_user()
#         if not user.verify_oath(user_info['id'], code):
#             return self.write_json(-3, '验证失败！')
#         else:
#             return self.write_json(0)
#
#
# class OathSecretQrCodeHandler(TPBaseUserAuthJsonHandler):
#     def get(self):
#         secret = self.get_session('tmp_oath_secret', None)
#
#         user_info = self.get_current_user()
#         img_data = tp_oath_generate_qrcode(user_info['name'], secret)
#
#         # secret = '6OHEKKJPLMUBJ4EHCT5ZT5YLUQ'
#         #
#         # print('TOPT should be:', get_totp_token(secret))
#         # # cur_input = int(time.time()) // 30
#         # # print('cur-input', cur_input, int(time.time()))
#         # # window = 10
#         # # for i in range(cur_input - (window - 1) // 2, cur_input + window // 2 + 1):  # [cur_input-(window-1)//2, cur_input + window//2]
#         # #     print(get_totp_token(secret, i))
#         #
#         # msg = 'otpauth://totp/Admin?secret={}&issuer=teleport'.format(secret)
#         # qr = qrcode.QRCode(
#         #     version=1,
#         #     error_correction=qrcode.constants.ERROR_CORRECT_L,
#         #     box_size=4,
#         #     border=4,
#         # )
#         # qr.add_data(msg)
#         # qr.make(fit=True)
#         # img = qr.make_image()
#         #
#         # # img = qrcode.make(msg)
#         # out = io.BytesIO()
#         # img.save(out, "jpeg", quality=100)
#         # # web.header('Content-Type','image/jpeg')
#         # # img.save('test.png')
#         self.set_header('Content-Type', 'image/jpeg')
#         self.write(img_data)
#
#
# class OathSecretResetHandler(TPBaseUserAuthJsonHandler):
#     def post(self):
#         oath_secret = tp_oath_generate_secret()
#         self.set_session('tmp_oath_secret', oath_secret)
#         return self.write_json(0, data={"tmp_oath_secret": oath_secret})
#
#
# class OathUpdateSecretHandler(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             try:
#                 args = json.loads(args)
#                 code = args['code']
#             except:
#                 return self.write_json(-2, '参数错误')
#         else:
#             return self.write_json(-1, '参数错误')
#
#         secret = self.get_session('tmp_oath_secret', None)
#         if secret is None:
#             return self.write_json(-1, '内部错误！')
#         self.del_session('tmp_oath_secret')
#
#         if tp_oath_verify_code(secret, code):
#             user_info = self.get_current_user()
#             try:
#                 ret = user.update_oath_secret(user_info['id'], secret)
#                 if 0 != ret:
#                     return self.write_json(ret)
#             except:
#                 log.e('update user oath-secret failed.')
#                 return self.write_json(-2, '发生异常')
#
#             # self.set_session('oath_secret', secret)
#             return self.write_json(0)
#         else:
#             return self.write_json(-3, '验证失败！')
