# -*- coding: utf-8 -*-

import json

from app.const import *
from app.base.configs import get_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.logger import log
from app.logic.auth.oath import tp_oath_generate_secret, tp_oath_generate_qrcode, tp_oath_verify_code
from app.logic.auth.captcha import tp_captcha_generate_image
from app.model import user
from app.model import syslog
from app.logic.auth.password import tp_password_verify


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
        args = self.get_argument('args', None)
        if args is not None:
            try:
                args = json.loads(args)
            except:
                return self.write_json(TPE_JSON_FORMAT, '参数错误')

            try:
                login_type = args['type']
                captcha = args['captcha'].strip()
                username = args['username'].strip()
                password = args['password']
                oath = args['oath'].strip()
                remember = args['remember']
            except:
                return self.write_json(TPE_PARAM, '参数错误')
        else:
            return self.write_json(TPE_PARAM, '参数错误')

        _tmp = {'username': username, 'surname': username}

        if login_type == LOGIN_TYPE_PASSWORD_CAPTCHA:
            oath = None
            code = self.get_session('captcha')
            if code is None:
                return self.write_json(TPE_CAPTCHA_EXPIRED, '验证码已失效')
            self.del_session('captcha')
            if code.lower() != captcha.lower():
                return self.write_json(TPE_CAPTCHA_MISMATCH, '验证码错误')
        elif login_type == LOGIN_TYPE_PASSWORD_OATH:
            if len(oath) == 0:
                return self.write_json(TPE_OATH_MISMATCH, '未提供身份验证器动态验证码')
        else:
            return self.write_json(TPE_PARAM, '参数错误')

        self.del_session('captcha')

        err, user_info = user.get_by_username(username)
        # if user_info is None:
        #     return self.write_json(TPE_USER_AUTH)
        if err != TPE_OK:
            if err == TPE_NOT_EXISTS:
                syslog.sys_log(_tmp, self.request.remote_ip, TPE_NOT_EXISTS, '登录失败，用户`{}`不存在'.format(username))
            return self.write_json(err)

        if user_info['state'] == USER_STATE_LOCKED:
            syslog.sys_log(_tmp, self.request.remote_ip, TPE_USER_LOCKED, '登录失败，用户已被锁定')
            return self.write_json(TPE_USER_LOCKED)
        elif user_info['state'] == USER_STATE_DISABLED:
            syslog.sys_log(_tmp, self.request.remote_ip, TPE_USER_DISABLED, '登录失败，用户已被禁用')
            return self.write_json(TPE_USER_DISABLED)
        elif user_info['state'] != USER_STATE_NORMAL:
            syslog.sys_log(_tmp, self.request.remote_ip, TPE_FAILED, '登录失败，系统内部错误')
            return self.write_json(TPE_FAILED)

        if login_type == LOGIN_TYPE_PASSWORD_CAPTCHA:
            if not tp_password_verify(password, user_info['password']):
                syslog.sys_log(_tmp, self.request.remote_ip, TPE_USER_AUTH, '登录失败，密码错误！')
                return self.write_json(TPE_USER_AUTH)
        elif login_type == LOGIN_TYPE_PASSWORD_OATH:
            if not tp_oath_verify_code(user_info['oath_secret'], oath):
                syslog.sys_log(_tmp, self.request.remote_ip, TPE_OATH_MISMATCH, "登录失败，身份验证器动态验证码错误！")
                return self.write_json(TPE_OATH_MISMATCH)

        self._user = user_info
        self._user['_is_login'] = True
        del self._user['password']
        del self._user['oath_secret']

        print('00000', self._user)

        if remember:
            self.set_session('user', self._user, 12 * 60 * 60)
        else:
            # TODO: 使用系统配置项中的默认会话超时
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
        code, img_data = tp_captcha_generate_image()
        self.set_session('captcha', code)
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
