# -*- coding: utf-8 -*-
import json

from eom_app.app.configs import app_cfg
from eom_app.module import host
from eom_app.module import user
from .base import SwxAuthJsonHandler, SwxAdminHandler, SwxAdminJsonHandler

cfg = app_cfg()


class IndexHandler(SwxAdminHandler):
    def get(self):
        self.render('user/index.mako')


class AuthHandler(SwxAdminHandler):
    def get(self, user_name):
        group_list = host.get_group_list()
        cert_list = host.get_cert_list()
        self.render('user/auth.mako',
                    group_list=group_list,
                    cert_list=cert_list, user_name=user_name)


class GetListHandler(SwxAdminJsonHandler):
    def post(self):
        user_list = user.get_user_list()
        ret = dict()
        ret['page_index'] = 10
        ret['total'] = len(user_list)
        ret['data'] = user_list
        self.write_json(0, data=ret)


class DeleteUser(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        user_id = args['user_id']
        try:
            ret = user.delete_user(user_id)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class ModifyUser(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return

        user_id = args['user_id']
        user_desc = args['user_desc']

        try:
            ret = user.modify_user(user_id, user_desc)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class AddUser(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        user_name = args['user_name']
        user_pwd = '123456'
        user_desc = args['user_desc']
        if user_desc is None:
            user_desc = ''
        try:
            ret = user.add_user(user_name, user_pwd, user_desc)
            self.write_json(ret)
            return
        except:
            self.write_json(-1)
            return


class LockUser(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        user_id = args['user_id']
        lock_status = args['lock_status']

        try:
            ret = user.lock_user(user_id, lock_status)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class ResetUser(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        user_id = args['user_id']
        # lock_status = args['lock_status']

        try:
            ret = user.reset_user(user_id)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class HostList(SwxAuthJsonHandler):
    def post(self):
        filter = dict()
        # user = self.get_current_user()
        order = dict()
        order['name'] = 'host_id'
        order['asc'] = True
        limit = dict()
        limit['page_index'] = 0
        limit['per_page'] = 25

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)

            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'host_sys_type' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'host_group' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            filter.update(_filter)
            # print('filter', filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            limit.update(_limit)

            _order = args['order']
            if _order is not None:
                order['name'] = _order['k']
                order['asc'] = _order['v']
        # filter['account_name'] = user['name']
        _total, _hosts = host.get_host_info_list_by_user(filter, order, limit)

        ret = dict()
        ret['page_index'] = limit['page_index']
        ret['total'] = _total
        ret['data'] = _hosts
        self.write_json(0, data=ret)


class AllocHost(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        user_name = args['user_name']
        host_list = args['host_list']
        try:
            ret = user.alloc_host(user_name, host_list)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
        except:
            self.write_json(-2)


class AllocHostUser(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        user_name = args['user_name']
        host_auth_id_list = args['host_list']
        try:
            ret = user.alloc_host_user(user_name, host_auth_id_list)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
        except:
            self.write_json(-2)


class DeleteHost(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        user_name = args['user_name']
        host_list = args['host_list']
        try:
            ret = user.delete_host(user_name, host_list)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
        except:
            self.write_json(-2)


class DeleteHostUser(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return
        user_name = args['user_name']
        auth_id_list = args['auth_id_list']
        try:
            ret = user.delete_host_user(user_name, auth_id_list)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
        except:
            self.write_json(-2)
