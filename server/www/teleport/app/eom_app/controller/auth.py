# -*- coding: utf-8 -*-

import json

from eom_app.app.const import *
from eom_app.app.configs import app_cfg
from eom_app.module import user
from eom_common.eomcore.logger import *
from .base import TPBaseHandler, TPBaseUserAuthHandler, TPBaseJsonHandler, TPBaseUserAuthJsonHandler
from eom_app.app.util import gen_captcha
from eom_app.app.oath import gen_oath_secret, gen_oath_qrcode, verify_oath_code


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
        # code = self.get_session('captcha')
        # if code is None:
        #     return self.write_json(-1, '验证码已失效')
        #
        # self.del_session('captcha')

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            login_type = args['type'].strip()
            captcha = args['captcha'].strip()
            username = args['username'].strip()
            password = args['password'].strip()
            oath = args['oath'].strip()
            remember = args['remember']
        else:
            return self.write_json(-1, '参数错误')

        if login_type == 'password':
            oath = None
            code = self.get_session('captcha')
            if code is None:
                return self.write_json(-1, '验证码已失效')
            self.del_session('captcha')
            if code.lower() != captcha.lower():
                return self.write_json(-1, '验证码错误')
        elif login_type == 'oath':
            if len(oath) == 0:
                return self.write_json(-1, '身份验证器动态验证码错误')

        self.del_session('captcha')

        try:
            user_id, account_type, nickname, locked = user.verify_user(username, password, oath)
            if locked == 1:
                return self.write_json(-1, '账号被锁定，请联系管理员！')
            if user_id == 0:
                if app_cfg().app_mode == APP_MODE_MAINTENANCE:
                    return self.write_json(-2, '系统维护中，请稍候再试！')
                else:
                    return self.write_json(-1, '用户名/密码错误！')

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
                self.set_session('user', _user, 12 * 60 * 60)
            else:
                self.set_session('user', _user)
            return self.write_json(0)

        except:
            log.e('can not set session.')
            return self.write_json(-1, '发生异常，无法登录！')


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
            return self.write_json(-1, '验证码已失效')

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            captcha = args['captcha']
        else:
            return self.write_json(-1, '参数错误')

        if code.lower() != captcha.lower():
            return self.write_json(-1, '验证码错误')

        return self.write_json(0)


class ModifyPwd(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')
        _old_pwd = args['o_pwd']
        _new_pwd = args['n_pwd']

        if _old_pwd is None or _new_pwd is None:
            return self.write_json(-2, '参数错误')

        user_info = self.get_current_user()
        try:
            ret = user.modify_pwd(_old_pwd, _new_pwd, user_info['id'])
            if 0 == ret:
                return self.write_json(0)
            else:
                return self.write_json(ret)
        except:
            log.e('modify password failed.')
            return self.write_json(-4, '发生异常')


class OathVerifyHandler(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            try:
                args = json.loads(args)
                code = args['code']
            except:
                return self.write_json(-2, '参数错误')
        else:
            return self.write_json(-1, '参数错误')

        # secret = self.get_session('tmp_oath_secret', None)
        # if secret is None:
        #     return self.write_json(-1, '内部错误！')
        # self.del_session('tmp_oath_secret')

        user_info = self.get_current_user()
        if not user.verify_oath(user_info['id'], code):
            return self.write_json(-3, '验证失败！')
        else:
            return self.write_json(0)


class OathSecretQrCodeHandler(TPBaseUserAuthJsonHandler):
    def get(self):
        secret = self.get_session('tmp_oath_secret', None)
        print('tmp-oath-secret:', secret)

        user_info = self.get_current_user()
        img_data = gen_oath_qrcode(user_info['name'], secret)

        # secret = '6OHEKKJPLMUBJ4EHCT5ZT5YLUQ'
        #
        # print('TOPT should be:', get_totp_token(secret))
        # # cur_input = int(time.time()) // 30
        # # print('cur-input', cur_input, int(time.time()))
        # # window = 10
        # # for i in range(cur_input - (window - 1) // 2, cur_input + window // 2 + 1):  # [cur_input-(window-1)//2, cur_input + window//2]
        # #     print(get_totp_token(secret, i))
        #
        # msg = 'otpauth://totp/Admin?secret={}&issuer=teleport'.format(secret)
        # qr = qrcode.QRCode(
        #     version=1,
        #     error_correction=qrcode.constants.ERROR_CORRECT_L,
        #     box_size=4,
        #     border=4,
        # )
        # qr.add_data(msg)
        # qr.make(fit=True)
        # img = qr.make_image()
        #
        # # img = qrcode.make(msg)
        # out = io.BytesIO()
        # img.save(out, "jpeg", quality=100)
        # # web.header('Content-Type','image/jpeg')
        # # img.save('test.png')
        self.set_header('Content-Type', 'image/jpeg')
        self.write(img_data)


class OathSecretResetHandler(TPBaseUserAuthJsonHandler):
    def post(self):
        oath_secret = gen_oath_secret()
        self.set_session('tmp_oath_secret', oath_secret)
        return self.write_json(0, data={"tmp_oath_secret": oath_secret})


class OathUpdateSecretHandler(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            try:
                args = json.loads(args)
                code = args['code']
            except:
                return self.write_json(-2, '参数错误')
        else:
            return self.write_json(-1, '参数错误')

        secret = self.get_session('tmp_oath_secret', None)
        if secret is None:
            return self.write_json(-1, '内部错误！')
        self.del_session('tmp_oath_secret')

        if verify_oath_code(secret, code):
            user_info = self.get_current_user()
            try:
                ret = user.update_oath_secret(user_info['id'], secret)
                if 0 != ret:
                    return self.write_json(ret)
            except:
                log.e('update user oath-secret failed.')
                return self.write_json(-2, '发生异常')

            # self.set_session('oath_secret', secret)
            return self.write_json(0)
        else:
            return self.write_json(-3, '验证失败！')
