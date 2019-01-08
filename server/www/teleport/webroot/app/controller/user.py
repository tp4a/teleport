# -*- coding: utf-8 -*-

import csv
import json
import os
import time

import tornado.gen
from app.base import mail
from app.base.configs import tp_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.logger import *
from app.base.session import tp_session
from app.base.utils import tp_check_strong_password, tp_gen_password
from app.logic.auth.oath import tp_oath_verify_code
from app.const import *
from app.logic.auth.oath import tp_oath_generate_secret, tp_oath_generate_qrcode
from app.logic.auth.password import tp_password_generate_secret, tp_password_verify
from app.model import group
from app.model import user


class UserListHandler(TPBaseHandler):
    def get(self):

        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        is_sys_smtp = False
        if tp_cfg().sys.loaded:
            smtp = tp_cfg().sys.smtp
            if len(smtp.server) > 0:
                is_sys_smtp = True

        param = {
            'sys_smtp': is_sys_smtp,
            'sys_cfg': tp_cfg().sys
        }

        self.render('user/user-list.mako', page_param=json.dumps(param))


class GroupListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
        if ret != TPE_OK:
            return
        self.render('user/user-group-list.mako')


class GroupInfoHandler(TPBaseHandler):
    def get(self, gid):
        ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
        if ret != TPE_OK:
            return
        gid = int(gid)
        err, groups = group.get_by_id(TP_GROUP_USER, gid)
        if err == TPE_OK:
            param = {
                'group_id': gid,
                'group_name': groups['name'],
                'group_desc': groups['desc']
            }
        else:
            param = {
                'group_id': 0,
                'group_name': '',
                'group_desc': ''
            }
        self.render('user/user-group-info.mako', page_param=json.dumps(param))


class MeHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_LOGIN_WEB)
        if ret != TPE_OK:
            return

        self.render('user/me.mako')


class ResetPasswordHandler(TPBaseHandler):
    def get(self):
        param = {
            'mode': 0,  # mode=0, unknown mode.
            'token': '',
            'code': TPE_OK
        }

        _token = self.get_argument('token', None)
        if _token is None:
            # 如果尚未设置SMTP或者系统限制，不允许发送密码重置邮件
            if len(tp_cfg().sys.smtp.server) == 0:
                param['mode'] = 2  # mode=2, show 'error' page
                param['code'] = TPE_NETWORK
            elif not tp_cfg().sys.password.allow_reset:
                param['mode'] = 2  # mode=2, show 'error' page
                param['code'] = TPE_PRIVILEGE
            else:
                param['mode'] = 1  # mode=1, show 'find-my-password' page.
        else:
            err, _ = user.check_reset_token(_token)

            param['code'] = err
            param['token'] = _token

            if err != TPE_OK:
                param['mode'] = 2  # mode=2, show 'error' page
            else:
                param['mode'] = 3  # mode=3, show 'set-new-password' page
                param['force_strong'] = tp_cfg().sys.password.force_strong

        self.render('user/reset-password.mako', page_param=json.dumps(param))


class BindOathHandler(TPBaseHandler):
    def get(self):
        self.render('user/bind-oath.mako')


class DoGenerateOathSecretHandler(TPBaseJsonHandler):
    def post(self):
        oath_secret = tp_oath_generate_secret()
        self.set_session('tmp_oath_secret', oath_secret)
        return self.write_json(TPE_OK, data={"tmp_oath_secret": oath_secret})


class DoVerifyUserHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            username = args['username']
            password = args['password']
        except:
            return self.write_json(TPE_PARAM)

        try:
            check_bind_oath = args['check_bind_oath']
        except:
            check_bind_oath = False

        err, user_info = user.login(self, username, password=password, check_bind_oath=check_bind_oath)
        if err != TPE_OK:
            if err == TPE_NOT_EXISTS:
                err = TPE_USER_AUTH
            return self.write_json(err)

        return self.write_json(TPE_OK)


class DoBindOathHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            username = args['username']
            password = args['password']
            oath_code = args['oath_code']
        except:
            return self.write_json(TPE_PARAM)

        err, user_info = user.login(self, username, password=password)
        if err != TPE_OK:
            if err == TPE_NOT_EXISTS:
                err = TPE_USER_AUTH
            return self.write_json(err)

        secret = self.get_session('tmp_oath_secret', None)
        if secret is None:
            return self.write_json(TPE_FAILED, '内部错误！')
        self.del_session('tmp_oath_secret')

        if not tp_oath_verify_code(secret, oath_code):
            return self.write_json(TPE_OATH_MISMATCH)

        err = user.update_oath_secret(self, user_info['id'], secret)
        if err != TPE_OK:
            return self.write_json(err)

        return self.write_json(TPE_OK)


class DoUnBindOathHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_DELETE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            users = args['users']
        except:
            return self.write_json(TPE_PARAM)

        # 把oath设置为空就是去掉oath验证
        err = user.update_oath_secret(self, users, '')
        self.write_json(err)


class OathSecretQrCodeHandler(TPBaseHandler):
    def get(self):
        username = self.get_argument('u', None)
        if username is None:
            user_info = self.get_current_user()
            username = user_info['username']

        username = username + '@teleport'

        secret = self.get_session('tmp_oath_secret', None)

        img_data = tp_oath_generate_qrcode(username, secret)

        self.set_header('Content-Type', 'image/jpeg')
        self.write(img_data)


class DoGetUserInfoHandler(TPBaseJsonHandler):
    def post(self, user_id):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE | TP_PRIVILEGE_USER_DELETE | TP_PRIVILEGE_USER_LOCK | TP_PRIVILEGE_USER_GROUP)
        if ret != TPE_OK:
            return

        err, info = user.get_user_info(user_id)
        self.write_json(err, data=info)


class DoGetUsersHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'username'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25
        sql_restrict = args['restrict'] if 'restrict' in args else {}
        sql_exclude = args['exclude'] if 'exclude' in args else {}

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'role' and _filter[i] == -1:
                    tmp.append(i)
                    continue
                if i == 'state' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            sql_limit.update(_limit)

            _order = args['order']
            if _order is not None:
                sql_order['name'] = _order['k']
                sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total_count, page_index, row_data = user.get_users(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoImportHandler(TPBaseHandler):
    IDX_USERNAME = 0
    IDX_SURNAME = 1
    IDX_EMAIL = 2
    IDX_MOBILE = 3
    IDX_QQ = 4
    IDX_WECHAT = 5
    IDX_GROUP = 6
    IDX_DESC = 7

    @tornado.gen.coroutine
    def post(self):
        """
        csv导入规则：
        每一行的数据格式：  用户账号,用户姓名,登录认证方式,email地址,Mobile,QQ,WeChat,所属组,描述
        在导入时：
          0. 以“#”作为行注释。
          1. 用户账号是必须填写的，其他均为可选。
          2. 一个用户属于多个组，可以用“|”将组分隔，如果某个组并不存在，则会创建这个组。
          3. 空行跳过，数据格式不正确的跳过。
        """

        ret = dict()
        ret['code'] = TPE_OK
        ret['message'] = ''

        rv = self.check_privilege(TP_PRIVILEGE_USER_CREATE | TP_PRIVILEGE_USER_GROUP, need_process=False)
        if rv != TPE_OK:
            ret['code'] = rv
            ret['code'] = rv
            if rv == TPE_NEED_LOGIN:
                ret['message'] = '需要登录！'
            elif rv == TPE_PRIVILEGE:
                ret['message'] = '权限不足！'
            else:
                ret['message'] = '未知错误！'
            return self.write(json.dumps(ret).encode('utf8'))

        success = list()
        failed = list()
        group_failed = list()
        csv_filename = ''

        try:
            upload_path = os.path.join(tp_cfg().data_path, 'tmp')  # 文件的暂存路径
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)
            file_metas = self.request.files['csvfile']  # 提取表单中‘name’为‘file’的文件元数据
            for meta in file_metas:
                now = time.localtime(time.time())
                tmp_name = 'upload-{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}.csv'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
                csv_filename = os.path.join(upload_path, tmp_name)
                with open(csv_filename, 'wb') as f:
                    f.write(meta['body'])

            # file encode maybe utf8 or gbk... check it out.
            file_encode = None
            with open(csv_filename, encoding='gbk') as f:
                try:
                    f.readlines()
                    file_encode = 'gbk'
                except:
                    pass

            if file_encode is None:
                log.v('file `{}` is not gbk, try utf8\n'.format(csv_filename))
                with open(csv_filename, encoding='utf_8_sig') as f:
                    try:
                        f.readlines()
                        file_encode = 'utf_8_sig'
                    except:
                        pass

            if file_encode is None:
                os.remove(csv_filename)
                log.e('file `{}` unknown encode, neither GBK nor UTF8.\n'.format(csv_filename))
                ret['code'] = TPE_FAILED
                ret['message'] = '文件无法解码：不是GBK编码或者UTF8编码！'
                return self.write(json.dumps(ret).encode('utf8'))

            group_list = dict()
            user_list = list()

            # 解析csv文件
            with open(csv_filename, encoding=file_encode) as f:
                username_list = []  # 用于检查是否有重复的用户被添加
                csv_reader = csv.reader(f)
                line = 0
                for csv_recorder in csv_reader:
                    line += 1

                    # 跳过空行和注释
                    if len(csv_recorder) == 0 or csv_recorder[0].strip().startswith('#'):
                        continue

                    # 格式错误则记录在案，然后继续
                    if len(csv_recorder) != 8:
                        failed.append({'line': line, 'error': '格式错误，字段数量不匹配。'})
                        continue

                    # check
                    _username = csv_recorder[self.IDX_USERNAME].strip()
                    if len(_username) == 0:
                        failed.append({'line': line, 'error': '格式错误，用户账号必须填写。'})
                        continue

                    _email = csv_recorder[self.IDX_EMAIL].strip()

                    _group = csv_recorder[self.IDX_GROUP].split('|')

                    u = dict()
                    u['_line'] = line
                    u['_id'] = 0
                    u['username'] = _username
                    u['surname'] = csv_recorder[self.IDX_SURNAME].strip()
                    # u['auth'] = _auth
                    u['email'] = _email
                    u['mobile'] = csv_recorder[self.IDX_MOBILE].strip()
                    u['qq'] = csv_recorder[self.IDX_QQ].strip()
                    u['wechat'] = csv_recorder[self.IDX_WECHAT].strip()
                    u['desc'] = csv_recorder[self.IDX_DESC].strip()

                    u['password'] = tp_gen_password(8)

                    # fix
                    if len(u['surname']) == 0:
                        u['surname'] = _username
                    u['username'] = _username.lower()
                    if u['username'] in username_list:
                        failed.append({'line': line, 'error': '上传文件中用户 `{}` 重复。'.format(u['username'])})
                        continue
                    else:
                        username_list.append(u['username'])

                    u['_group'] = list()
                    for i in range(len(_group)):
                        x = _group[i].strip()
                        if len(x) > 0:
                            u['_group'].append(x)

                    # 更新一下组列表，以备后续为用户与所在组创建映射
                    for i in range(len(u['_group'])):
                        if u['_group'][i] not in group_list:
                            group_list[u['_group'][i]] = 0

                    user_list.append(u)

            if os.path.exists(csv_filename):
                os.remove(csv_filename)

            # 检查一下
            if len(user_list) == 0:
                ret['code'] = TPE_FAILED
                ret['message'] = '上传的 csv 文件中没有可用于导入的用户！'
                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))

            # 已经有了用户组列表，查询组数据库，有则更新用户组列表中组对应的id，无则创建组
            if len(group_list) > 0:
                err = group.make_groups(self, TP_GROUP_USER, group_list, group_failed)
                if len(group_failed) > 0:
                    ret['code'] = TPE_FAILED
                    ret['message'] += '无法创建用户组 {}。'.format('，'.join(group_failed))
                    return self.write(json.dumps(ret).encode('utf8'))

            # 对用户列表中的每一项，创建用户
            user.create_users(self, user_list, success, failed)

            # 对创建成功的用户，在用户组映射表中设定其对应关系
            gm = list()
            for u in user_list:
                if u['_id'] == 0:
                    continue
                for ug in u['_group']:
                    for g in group_list:
                        if group_list[g] == 0 or ug != g:
                            continue
                        gm.append({'type': TP_GROUP_USER, 'gid': group_list[g], 'mid': u['_id']})

            group.make_group_map(TP_GROUP_USER, gm)

            # 对于创建成功的用户，发送密码邮件函
            sys_smtp_password = tp_cfg().sys_smtp_password
            if len(sys_smtp_password) > 0:
                web_url = '{}://{}'.format(self.request.protocol, self.request.host)
                for u in user_list:
                    if u['_id'] == 0 or len(u['email']) == 0:
                        continue
                    err, msg = yield mail.tp_send_mail(
                        u['email'],
                        '{surname} 您好！\n\n已为您创建teleport系统用户账号，现在可以使用以下信息登录teleport系统：\n\n'
                        '登录用户名：{username}\n'
                        '密码：{password}\n'
                        '地址：{web_url}\n\n\n\n'
                        '[本邮件由teleport系统自动发出，请勿回复]'
                        '\n\n'
                        ''.format(surname=u['surname'], username=u['username'], password=u['password'], web_url=web_url),
                        subject='用户密码函'
                    )
                    if err != TPE_OK:
                        failed.append({'line': u['_line'], 'error': '无法发送密码函到邮箱 {}，错误：{}。'.format(u['email'], msg)})

            # 统计结果
            total_success = 0
            total_failed = 0
            for u in user_list:
                if u['_id'] == 0:
                    total_failed += 1
                else:
                    total_success += 1

            # 生成最终结果信息
            if len(failed) == 0:
                ret['code'] = TPE_OK
                ret['message'] = '共导入 {} 个用户账号！'.format(total_success)
                return self.write(json.dumps(ret).encode('utf8'))
            else:
                ret['code'] = TPE_FAILED
                if total_success > 0:
                    ret['message'] = '{} 个用户账号导入成功，'.format(total_success)
                if total_failed > 0:
                    ret['message'] += '{} 个用户账号未能导入！'.format(total_failed)

                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))
        except:
            log.e('got exception when import user.\n')
            ret['code'] = TPE_FAILED
            if len(success) > 0:
                ret['message'] += '{} 个用户账号导入后发生异常！'.format(len(success))
            else:
                ret['message'] = '发生异常！'

            ret['data'] = failed
            return self.write(json.dumps(ret).encode('utf8'))


class DoUpdateUserHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            args['id'] = int(args['id'])
            args['role'] = int(args['role'])
            args['auth_type'] = int(args['auth_type'])
            args['username'] = args['username'].strip().lower()
            args['surname'] = args['surname'].strip()
            args['email'] = args['email'].strip()
            args['mobile'] = args['mobile'].strip()
            args['qq'] = args['qq'].strip()
            args['wechat'] = args['wechat'].strip()
            args['desc'] = args['desc'].strip()
        except:
            return self.write_json(TPE_PARAM)

        if len(args['username']) == 0:
            return self.write_json(TPE_PARAM)

        if args['id'] == -1:
            args['password'] = tp_gen_password(8)
            err, _ = user.create_user(self, args)
            if err == TPE_OK:
                if len(args['email']) == 0:
                    return self.write_json(TPE_OK)

                # 对于创建成功的用户，发送密码邮件函
                sys_smtp_password = tp_cfg().sys_smtp_password
                if len(sys_smtp_password) > 0:
                    web_url = '{}://{}'.format(self.request.protocol, self.request.host)
                    err, msg = yield mail.tp_send_mail(
                        args['email'],
                        '{surname} 您好！\n\n已为您创建teleport系统用户账号，现在可以使用以下信息登录teleport系统：\n\n'
                        '登录用户名：{username}\n'
                        '密码：{password}\n'
                        '地址：{web_url}\n\n\n\n'
                        '[本邮件由teleport系统自动发出，请勿回复]'
                        '\n\n'
                        ''.format(surname=args['surname'], username=args['username'], password=args['password'], web_url=web_url),
                        subject='用户密码函'
                    )
                    if err != TPE_OK:
                        return self.write_json(TPE_OK, '用户账号创建成功，但发送密码函失败：{}'.format(msg))
                    else:
                        return self.write_json(TPE_OK)
            else:
                return self.write_json(err)
        else:
            err = user.update_user(self, args)
            self.write_json(err)


class DoSetRoleForUsersHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            users = args['users']
            role_id = int(args['role_id'])
        except:
            return self.write_json(TPE_PARAM)

        if len(users) == 0 or role_id == 0:
            return self.write_json(TPE_PARAM)

        err = user.set_role_for_users(self, users, role_id)
        self.write_json(err)


class DoResetPasswordHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            mode = int(args['mode'])
        except:
            return self.write_json(TPE_PARAM)

        password = ''

        if mode == 1:
            # 管理员直接在后台给用户发送密码重置邮件
            err = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
            if err != TPE_OK:
                return self.write_json(err)

            try:
                user_id = int(args['id'])
            except:
                return self.write_json(TPE_PARAM)

        elif mode == 2:
            # 管理员直接在后台为用户重置密码
            err = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
            if err != TPE_OK:
                return self.write_json(err)

            try:
                user_id = int(args['id'])
                password = args['password']
            except:
                return self.write_json(TPE_PARAM)

        elif mode == 3:
            # 用户自行找回密码，需要填写用户名、邮箱、验证码
            try:
                username = args['username']
                email = args['email']
                captcha = args['captcha']
            except:
                return self.write_json(TPE_PARAM)

            code = self.get_session('captcha')
            if code is None:
                return self.write_json(TPE_CAPTCHA_EXPIRED, '验证码已失效')
            if code.lower() != captcha.lower():
                return self.write_json(TPE_CAPTCHA_MISMATCH, '验证码错误')

            self.del_session('captcha')
            err, user_info = user.get_by_username(username)
            if err != TPE_OK:
                return self.write_json(err)
            if user_info.email != email:
                return self.write_json(TPE_NOT_EXISTS)

            user_id = user_info.id

        elif mode == 4:
            # 用户通过密码重置邮件中的链接（有token验证），在页面上设置新密码，需要提供token、新密码
            try:
                token = args['token']
                password = args['password']
            except:
                return self.write_json(TPE_PARAM)

            err, user_id = user.check_reset_token(token)
            if err != TPE_OK:
                return self.write_json(err)

        elif mode == 5:
            # 用户输入当前密码和新密码进行设置
            try:
                current_password = args['current_password']
                password = args['password']
            except:
                return self.write_json(TPE_PARAM)

            err, user_info = user.get_by_username(self.get_current_user()['username'])
            if err != TPE_OK:
                return self.write_json(err)
            if not tp_password_verify(current_password, user_info['password']):
                return self.write_json(TPE_USER_AUTH)
            user_id = user_info['id']

        else:
            return self.write_json(TPE_PARAM)

        if user_id == 0:
            return self.write_json(TPE_PARAM)

        if mode == 1 or mode == 3:
            err, email, token = user.generate_reset_password_token(self, user_id)

            # generate an URL for reset password, valid in 24hr.
            reset_url = '{}://{}/user/reset-password?token={}'.format(self.request.protocol, self.request.host, token)

            err, msg = yield mail.tp_send_mail(
                email,
                'Teleport用户，您好！\n\n请访问以下链接以重设您的teleport登录密码。此链接将于本邮件寄出24小时之后失效。\n'
                '访问此链接，将会为您打开密码重置页面，然后您可以设定新密码。\n\n'
                '如果您并没有做重设密码的操作，请忽略本邮件，请及时联系您的系统管理员！\n\n'
                '{reset_url}\n\n\n\n'
                '[本邮件由teleport系统自动发出，请勿回复]'
                '\n\n'
                ''.format(reset_url=reset_url),
                subject='密码重置确认函'
            )

            return self.write_json(err, msg)

        elif mode == 2 or mode == 4 or mode == 5:
            if len(password) == 0:
                return self.write_json(TPE_PARAM)

            # 根据需要进行弱密码检测
            if tp_cfg().sys.password.force_strong:
                if not tp_check_strong_password(password):
                    return self.write_json(TPE_FAILED, '密码强度太弱！强密码需要至少8个英文字符，必须包含大写字母、小写字母和数字。')

            password = tp_password_generate_secret(password)
            err = user.set_password(self, user_id, password)

            if mode == 4 and err == TPE_OK:
                user.remove_reset_token(token)

            # 非用户自行修改密码的情况，都默认重置身份认证
            if mode != 5 and err == TPE_OK:
                print("reset oath secret")
                user.update_oath_secret(self, user_id, '')

            self.write_json(err)

        else:
            self.write_json(TPE_PARAM)


class DoUpdateUsersHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_DELETE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            action = args['action']
            users = args['users']
        except:
            return self.write_json(TPE_PARAM)

        if action == 'lock':
            err = user.update_users_state(self, users, TP_STATE_DISABLED)
        elif action == 'unlock':
            err = user.update_users_state(self, users, TP_STATE_NORMAL)
        elif action == 'remove':
            err = user.remove_users(self, users)
        else:
            err = TPE_PARAM

        if err != TPE_OK:
            return self.write_json(err)

        # force logout if user LOCKED or REMOVED.
        if action == 'lock' or action == 'remove':
            v = tp_session().get_start_with('user-')
            for k in v:
                if v[k]['v']['id'] in users:
                    tp_session().taken(k)

        self.write_json(err)


class DoGetGroupWithMemberHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'name'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            sql_limit.update(_limit)

            _order = args['order']
            if _order is not None:
                sql_order['name'] = _order['k']
                sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total_count, row_data = user.get_group_with_member(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = sql_limit['page_index']
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoGetRoleListHandler(TPBaseJsonHandler):
    def post(self):
        err, role_list = user.get_role_list()
        if err != TPE_OK:
            self.write_json(err)
        else:
            self.write_json(TPE_OK, data=role_list)
