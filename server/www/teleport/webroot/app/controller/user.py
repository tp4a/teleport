# -*- coding: utf-8 -*-

import os
import json
import time
import csv

from app.const import *
from app.base.configs import get_cfg
# from app.module import host
from app.base import mail
from app.model import user
from app.model import group
from app.logic.auth.password import tp_password_generate_secret
import tornado.gen
from app.base.logger import *
from app.base.controller import TPBaseHandler, TPBaseJsonHandler


# , TPBaseAdminAuthHandler, TPBaseAdminAuthJsonHandler

# cfg = get_cfg()


# class IndexHandler(TPBaseHandler):
#     def get(self):
#         ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE | TP_PRIVILEGE_USER_GROUP)
#         if ret != TPE_OK:
#             return
#         self.render('user/index.mako')

class UserListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE)
        if ret != TPE_OK:
            return

        is_sys_smtp = False
        if get_cfg().sys.loaded:
            smtp = get_cfg().sys.smtp
            if len(smtp.server) > 0 and smtp.port != -1:
                is_sys_smtp = True

        param = {
            'sys_smtp': is_sys_smtp
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
    IDX_AUTH_TYPE = 2
    IDX_EMAIL = 3
    IDX_MOBILE = 4
    IDX_QQ = 5
    IDX_WECHAT = 6
    IDX_GROUP = 7
    IDX_DESC = 8

    @tornado.gen.coroutine
    def post(self):
        """
        csv导入规则：
        每一行的数据格式：  用户账号,用户姓名,登录认证方式,email地址,Mobile,QQ,WeChat,所属组,描述
        在导入时：
          0. 以“#”作为行注释。
          1. 用户账号和email地址是必须填写的，其他均为可选。
          2. 一个用户属于多个组，可以用“|”将组分隔，如果某个组并不存在，则会创建这个组。
          3. 空行跳过，数据格式不正确的跳过。
        """
        ret = self.check_privilege(TP_PRIVILEGE_USER_CREATE | TP_PRIVILEGE_USER_GROUP)
        if ret != TPE_OK:
            return

        success = list()
        failed = list()
        group_failed = list()

        ret = dict()
        ret['code'] = TPE_OK
        ret['message'] = ''
        csv_filename = ''

        try:
            upload_path = os.path.join(get_cfg().data_path, 'tmp')  # 文件的暂存路径
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
                with open(csv_filename, encoding='utf8') as f:
                    try:
                        f.readlines()
                        file_encode = 'utf8'
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
                    if len(csv_recorder) != 9:
                        failed.append({'line': line, 'error': '格式错误，字段数量不匹配。'})
                        continue

                    # check
                    _username = csv_recorder[self.IDX_USERNAME].strip()
                    if len(_username) == 0:
                        failed.append({'line': line, 'error': '格式错误，用户账号必须填写。'})
                        continue

                    _auth = csv_recorder[self.IDX_AUTH_TYPE].strip()
                    if len(_auth) == 0:
                        failed.append({'line': line, 'error': '格式错误，用户认证类型必须填写。'})
                        continue
                    try:
                        _auth = int(_auth)
                    except:
                        failed.append({'line': line, 'error': '格式错误，用户认证类型必须是数字。'})
                        continue

                    _email = csv_recorder[self.IDX_EMAIL].strip()
                    # if len(_email) == 0:
                    #     failed.append({'line': line, 'error': '格式错误，用户邮箱必须填写。'})
                    #     continue

                    _group = csv_recorder[self.IDX_GROUP].split('|')

                    u = dict()
                    u['_line'] = line
                    u['_id'] = 0
                    u['username'] = _username
                    u['surname'] = csv_recorder[self.IDX_SURNAME].strip()
                    u['auth'] = _auth
                    u['email'] = _email
                    u['mobile'] = csv_recorder[self.IDX_MOBILE].strip()
                    u['qq'] = csv_recorder[self.IDX_QQ].strip()
                    u['wechat'] = csv_recorder[self.IDX_WECHAT].strip()
                    u['desc'] = csv_recorder[self.IDX_DESC].strip()

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

            if len(failed) == 0:
                ret['code'] = TPE_OK
                ret['message'] = '所有 {} 个用户账号均已导入！'.format(len(success))
                return self.write(json.dumps(ret).encode('utf8'))
            else:
                ret['code'] = TPE_FAILED
                if len(success) > 0:
                    ret['message'] = '{} 个用户账号导入成功，'.format(len(success))
                ret['message'] += '{} 个用户账号未能导入！'.format(len(failed))

                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))
        except:
            log.e('got exception when import user.\n')
            ret['code'] = TPE_FAILED
            if len(success) > 0:
                ret['message'] += '{} 个用户账号导入后发生异常！'.format(len(success))
            else:
                ret['message'] = '发生异常！'
            if len(failed) > 0:
                ret['data'] = failed
            return self.write(json.dumps(ret).encode('utf8'))

        finally:
            if os.path.exists(csv_filename):
                os.remove(csv_filename)


class DoUpdateUserHandler(TPBaseJsonHandler):
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
            args['username'] = args['username'].strip()
            args['surname'] = args['surname'].strip()
            args['email'] = args['email'].strip()
            args['mobile'] = args['mobile'].strip()
            args['qq'] = args['qq'].strip()
            args['wechat'] = args['wechat'].strip()
            args['desc'] = args['desc'].strip()
        except:
            return self.write_json(TPE_PARAM)

        if len(args['username']) == 0:  # or len(args['email']) == 0:
            return self.write_json(TPE_PARAM)

        if args['id'] == -1:
            err, info = user.create_user(self, args)
        else:
            err = user.update_user(self, args)
            info = {}
        self.write_json(err, data=info)


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
            user_id = int(args['id'])
            mode = int(args['mode'])
            email = args['email'].strip()
            password = args['password']
        except:
            return self.write_json(TPE_PARAM)

        if user_id == 0:
            return self.write_json(TPE_PARAM)

        if mode == 1:
            if len(email) == 0:
                return self.write_json(TPE_PARAM)

            # 生成一个密码重置链接，24小时有效
            reset_url = 'http://127.0.0.1/user/validate-password-reset-token?token=G66LXH0EOJ47OXTH7O5KBQ0PHXRSBXBVVFALI6JBJ8HNWUALWI35QECPJ8UV8DEQ'

            err, msg = yield mail.tp_send_mail(
                email,
                '您好！\n\n请访问以下链接以重设您的TELEPORT登录密码。此链接将于本邮件寄出24小时之后失效。访问此链接，将会为您打开密码重置页面，然后您可以设定新密码。\n\n'
                '如果您并没有做重设密码的操作，请及时联系系统管理员！\n\n'
                '{reset_url}\n\n'
                '\n\n'
                ''.format(reset_url=reset_url),
                subject='密码重置邮件'
            )

            return self.write_json(err, msg)

        elif mode == 2:
            if len(password) == 0:
                return self.write_json(TPE_PARAM)

            password = tp_password_generate_secret(password)
            err = user.set_password(self, user_id, password)

            self.write_json(err)

        else:
            self.write_json(TPE_PARAM)


class DoRemoveUserHandler(TPBaseJsonHandler):
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

        err = user.remove_users(self, users)
        self.write_json(err)


# class DoRemoveGroupHandler(TPBaseJsonHandler):
#     def post(self):
#         ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
#         if ret != TPE_OK:
#             return
#
#         args = self.get_argument('args', None)
#         if args is None:
#             return self.write_json(TPE_PARAM)
#         try:
#             args = json.loads(args)
#         except:
#             return self.write_json(TPE_JSON_FORMAT)
#
#         try:
#             group_list = args['group_list']
#         except:
#             return self.write_json(TPE_PARAM)
#
#         err = user.remove_group(self, group_list)
#         self.write_json(err)


# class AuthHandler(TPBaseAdminAuthHandler):
#     def get(self, user_name):
#         group_list = host.get_group_list()
#         cert_list = host.get_cert_list()
#         self.render('user/auth.mako',
#                     group_list=group_list,
#                     cert_list=cert_list, user_name=user_name)
#
#
# class GetListHandler(TPBaseAdminAuthJsonHandler):
#     def post(self):
#         user_list = user.get_user_list(with_admin=False)
#         ret = dict()
#         ret['page_index'] = 10
#         ret['total'] = len(user_list)
#         ret['data'] = user_list
#         self.write_json(0, data=ret)
#
#
# class DeleteUser(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, 'invalid param')
#
#         user_id = args['user_id']
#         try:
#             ret = user.delete_user(user_id)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-2, 'database op failed.')
#         except:
#             log.e('delete user failed.\n')
#             return self.write_json(-3, 'got exception.')
#
#
# class ModifyUser(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, 'invalid param.')
#
#         user_id = args['user_id']
#         user_desc = args['user_desc']
#
#         try:
#             ret = user.modify_user(user_id, user_desc)
#             if ret:
#                 self.write_json(0)
#             else:
#                 self.write_json(-2, 'database op failed.')
#             return
#         except:
#             log.e('modify user failed.\n')
#             self.write_json(-3, 'got exception.')
#
#
# class AddUser(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, 'invalid param.')
#
#         user_name = args['user_name']
#         user_pwd = '123456'
#         user_desc = args['user_desc']
#         if user_desc is None:
#             user_desc = ''
#         try:
#             ret = user.add_user(user_name, user_pwd, user_desc)
#             if 0 == ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(ret, 'database op failed. errcode={}'.format(ret))
#         except:
#             log.e('add user failed.\n')
#             return self.write_json(-3, 'got exception.')
#
#
# class LockUser(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, 'invalid param.')
#
#         user_id = args['user_id']
#         lock_status = args['lock_status']
#
#         try:
#             ret = user.lock_user(user_id, lock_status)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-2, 'database op failed.')
#         except:
#             log.e('lock user failed.\m')
#             return self.write_json(-3, 'got exception.')
#
#
# class ResetUser(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, 'invalid param.')
#
#         user_id = args['user_id']
#         # lock_status = args['lock_status']
#
#         try:
#             ret = user.reset_user(user_id)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-2, 'database op failed.')
#         except:
#             log.e('reset user failed.\n')
#             return self.write_json(-3, 'got exception.')
#

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


# class DoAddGroupMemberHandler(TPBaseJsonHandler):
#     def post(self):
#         ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
#         if ret != TPE_OK:
#             return
#
#         args = self.get_argument('args', None)
#         if args is None:
#             return self.write_json(TPE_PARAM)
#         try:
#             args = json.loads(args)
#         except:
#             return self.write_json(TPE_JSON_FORMAT)
#
#         try:
#             gid = args['group_id']
#             members = args['members']
#         except:
#             return self.write_json(TPE_PARAM)
#
#         err = user.add_group_members(gid, members)
#         self.write_json(err)


# class DoRemoveGroupMemberHandler(TPBaseJsonHandler):
#     def post(self):
#         ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
#         if ret != TPE_OK:
#             return
#
#         args = self.get_argument('args', None)
#         if args is None:
#             return self.write_json(TPE_PARAM)
#         try:
#             args = json.loads(args)
#         except:
#             return self.write_json(TPE_JSON_FORMAT)
#
#         try:
#             gid = args['group_id']
#             members = args['members']
#         except:
#             return self.write_json(TPE_PARAM)
#
#         err = user.remove_group_members(gid, members)
#         self.write_json(err)


# class DoUpdateGroupHandler(TPBaseJsonHandler):
#     def post(self):
#         ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
#         if ret != TPE_OK:
#             return
#
#         args = self.get_argument('args', None)
#         if args is None:
#             return self.write_json(TPE_PARAM)
#         try:
#             args = json.loads(args)
#         except:
#             return self.write_json(TPE_JSON_FORMAT)
#
#         try:
#             args['id'] = int(args['id'])
#             args['name'] = args['name'].strip()
#             args['desc'] = args['desc'].strip()
#         except:
#             return self.write_json(TPE_PARAM)
#
#         if len(args['name']) == 0:
#             return self.write_json(TPE_PARAM)
#
#         if args['id'] == -1:
#             err, _ = user.create_group(self, args)
#         else:
#             err = user.update_group(self, args)
#         self.write_json(err)


class DoGetRoleListHandler(TPBaseJsonHandler):
    def post(self):
        err, role_list = user.get_role_list()
        if err != TPE_OK:
            self.write_json(err)
        else:
            self.write_json(TPE_OK, data=role_list)
