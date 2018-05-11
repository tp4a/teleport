# -*- coding: utf-8 -*-

import json
import threading

import tornado.gen
import tornado.httpclient
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.core_server import core_service_async_enc
from app.base.logger import *
from app.const import *
from app.model import account
from app.model import group

# 临时认证ID的基数，每次使用时均递减
tmp_auth_id_base = -1
tmp_auth_id_lock = threading.RLock()


class AccGroupListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_ACCOUNT_GROUP)
        if ret != TPE_OK:
            return
        self.render('asset/account-group-list.mako')


class DoGetAccountsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ACCOUNT)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        # 如果只给出host_id参数，则表示获取此主机相关的所有账号
        if len(args) == 1 and 'host_id' in args:
            host_id = int(args['host_id'])
            err, row_data = account.get_host_accounts(host_id)
            return self.write_json(err, data=row_data)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'username'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 0
        sql_restrict = args['restrict'] if 'restrict' in args else {}
        sql_exclude = args['exclude'] if 'exclude' in args else {}

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                # if i == 'role' and _filter[i] == 0:
                #     tmp.append(i)
                #     continue
                # if i == 'host_state' and _filter[i] == 0:
                #     tmp.append(i)
                #     continue
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

        err, total_count, page_index, row_data = account.get_accounts(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoGetAccountGroupWithMemberHandler(TPBaseJsonHandler):
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
        sql_order['name'] = 'id'
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

        err, total_count, page_index, row_data = account.get_group_with_member(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)


class AccGroupInfoHandler(TPBaseHandler):
    def get(self, gid):
        ret = self.check_privilege(TP_PRIVILEGE_ACCOUNT_GROUP)
        if ret != TPE_OK:
            return
        gid = int(gid)
        err, groups = group.get_by_id(TP_GROUP_ACCOUNT, gid)
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

        self.render('asset/account-group-info.mako', page_param=json.dumps(param))


class DoUpdateAccountHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ACCOUNT | TP_PRIVILEGE_ACCOUNT_GROUP)
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
            host_id = int(args['host_id'])
            acc_id = int(args['acc_id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        try:
            param = dict()
            param['host_ip'] = args['param']['host_ip']
            param['router_ip'] = args['param']['router_ip']
            param['router_port'] = args['param']['router_port']
            param['protocol_type'] = int(args['param']['protocol'])
            param['protocol_port'] = int(args['param']['port'])
            param['auth_type'] = int(args['param']['auth_type'])
            param['username'] = args['param']['username'].strip()
            param['password'] = args['param']['password']
            param['pri_key'] = args['param']['pri_key'].strip()
            param['username_prompt'] = args['param']['username_prompt'].strip()
            param['password_prompt'] = args['param']['password_prompt'].strip()
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if len(param['username']) == 0:
            return self.write_json(TPE_PARAM)

        if acc_id == -1:
            # 新增账号
            if param['auth_type'] == TP_AUTH_TYPE_PASSWORD and len(param['password']) == 0:
                return self.write_json(TPE_PARAM)
            elif param['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY and len(param['pri_key']) == 0:
                return self.write_json(TPE_PARAM)

        if param['auth_type'] == TP_AUTH_TYPE_PASSWORD and len(param['password']) > 0:
            code, ret_data = yield core_service_async_enc(param['password'])
            if code != TPE_OK:
                return self.write_json(code)
            else:
                param['password'] = ret_data
        elif param['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY and len(param['pri_key']) > 0:
            code, ret_data = yield core_service_async_enc(param['pri_key'])
            if code != TPE_OK:
                return self.write_json(code, '无法加密存储私钥！')
            else:
                param['pri_key'] = ret_data

        if acc_id == -1:
            err, info = account.add_account(self, host_id, param)
        else:
            err = account.update_account(self, host_id, acc_id, param)
            info = {}

        self.write_json(err, data=info)


class DoUpdateAccountsHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ACCOUNT | TP_PRIVILEGE_ACCOUNT_GROUP)
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
            host_id = int(args['host_id'])
            accounts = args['accounts']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if action == 'remove':
            err = account.remove_accounts(self, host_id, accounts)
            return self.write_json(err)
        elif action == 'lock':
            err = account.update_accounts_state(self, host_id, accounts, TP_STATE_DISABLED)
            return self.write_json(err)
        elif action == 'unlock':
            err = account.update_accounts_state(self, host_id, accounts, TP_STATE_NORMAL)
            return self.write_json(err)
        else:
            return self.write_json(TPE_PARAM)
