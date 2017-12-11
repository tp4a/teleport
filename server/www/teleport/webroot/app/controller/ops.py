# -*- coding: utf-8 -*-

import json
import threading
import time

import tornado.gen
import tornado.httpclient
from app.base.logger import log
from app.base.configs import tp_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.core_server import *
from app.base.session import tp_session
from app.const import *
from app.model import account
from app.model import host
from app.model import ops

# 连接信息ID的基数，每次使用时均递增
tmp_conn_id_base = int(time.time())
tmp_conn_id_lock = threading.RLock()


class AuzListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS | TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return
        self.render('ops/auz-list.mako')


class RemoteHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS)
        if ret != TPE_OK:
            return
        self.render('ops/remote-list.mako')


class PolicyDetailHandler(TPBaseHandler):
    def get(self, pid):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return
        pid = int(pid)
        err, policy = ops.get_by_id(pid)
        if err == TPE_OK:
            param = {
                'policy_id': pid,
                'policy_name': policy['name'],
                'policy_desc': policy['desc'],
                'policy_flags': {
                    'record': policy['flag_record'],
                    'rdp': policy['flag_rdp'],
                    'ssh': policy['flag_ssh']
                }
            }
        else:
            param = {
                'policy_id': 0,
                'policy_name': '',
                'policy_desc': '',
                'policy_flags': {
                    'record': 0,
                    'rdp': 0,
                    'ssh': 0
                }
            }
        self.render('ops/auz-info.mako', page_param=json.dumps(param))


class SessionListsHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS | TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return
        self.render('ops/sessions.mako')


class DoGetSessionIDHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_OPS | TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        # 有三种方式获取会话ID：
        # 1. 给定一个远程连接授权ID（普通用户进行远程连接）
        # 2. 给定要连接的主机ID和账号ID（管理员进行远程连接）
        # 3. 给定要连接的主机ID和账号信息（管理员测试远程连接是否可用）
        #
        # WEB服务根据上述信息产生临时的远程连接ID，核心服务通过此远程连接ID来获取远程连接所需数据，生成会话ID。

        conn_info = dict()
        conn_info['_enc'] = 1
        conn_info['host_id'] = 0
        conn_info['client_ip'] = self.request.remote_ip
        conn_info['user_id'] = self.get_current_user()['id']
        conn_info['user_username'] = self.get_current_user()['username']

        protocol_sub_type = TP_PROTOCOL_TYPE_UNKNOWN

        if 'auth_id' in args:
            if 'protocol_sub_type' not in args:
                return self.write_json(TPE_PARAM)

            auth_id = args['auth_id']
            protocol_sub_type = int(args['protocol_sub_type'])
            ops_auth, err = ops.get_auth(auth_id)

            # TODO: 根据auth_id从数据库中取得此授权相关的用户、主机、账号三者详细信息
            acc_id = ops_auth['a_id']
            host_id = ops_auth['h_id']
            user_id = ops_auth['u_id']

            # TODO: 如果当前用户具有管理权限，则替换上述信息中的用户信息，否则检查当前用户是否是授权的用户
            # TODO: 条件均满足的情况下，将主机、账号信息放入临时授权信息中（仅10秒有效期），并生产一个临时授权ID
            # TODO: 核心服务通过此临时授权ID来获取远程连接认证数据，生成会话ID。

            err, acc_info = account.get_account_info(acc_id)
            if err != TPE_OK:
                return self.write_json(err)
            log.v(acc_info)

        elif len(args) == 2 and 'acc_id' in args and 'host_id' in args:
            acc_id = args['acc_id']
            host_id = args['host_id']

            err, acc_info = account.get_account_info(acc_id)
            if err != TPE_OK:
                return self.write_json(err)

        else:
            conn_info['_test'] = 1
            try:
                acc_id = int(args['acc_id'])
                host_id = int(args['host_id'])
                auth_type = int(args['auth_type'])
                username = args['username']
                password = args['password']
                pri_key = args['pri_key']
                protocol_type = int(args['protocol_type'])
                protocol_sub_type = int(args['protocol_sub_type'])
                protocol_port = int(args['protocol_port'])
            except:
                return self.write_json(TPE_PARAM)

            if len(username) == 0:
                return self.write_json(TPE_PARAM)

            acc_info = dict()

            acc_info['auth_type'] = auth_type
            acc_info['protocol_type'] = protocol_type
            acc_info['protocol_port'] = protocol_port
            acc_info['username'] = username

            acc_info['password'] = password
            acc_info['pri_key'] = pri_key

            conn_info['_enc'] = 0

            if acc_id == -1:
                if auth_type == TP_AUTH_TYPE_PASSWORD and len(password) == 0:
                    return self.write_json(TPE_PARAM)
                elif auth_type == TP_AUTH_TYPE_PRIVATE_KEY and len(pri_key) == 0:
                    return self.write_json(TPE_PARAM)
            else:
                if (auth_type == TP_AUTH_TYPE_PASSWORD and len(password) == 0) or (auth_type == TP_AUTH_TYPE_PRIVATE_KEY and len(pri_key) == 0):
                    err, _acc_info = account.get_account_info(acc_id)
                    if err != TPE_OK:
                        return self.write_json(err)
                    acc_info['password'] = _acc_info['password']
                    acc_info['pri_key'] = _acc_info['pri_key']

                    conn_info['_enc'] = 1

        # 获取要远程连接的主机信息（要访问的IP地址，如果是路由模式，则是路由主机的IP+端口）
        err, host_info = host.get_host_info(host_id)
        if err != TPE_OK:
            return self.write_json(err)

        conn_info['host_id'] = host_id
        conn_info['host_ip'] = host_info['ip']
        if len(host_info['router_ip']) > 0:
            conn_info['conn_ip'] = host_info['router_ip']
            conn_info['conn_port'] = host_info['router_port']
        else:
            conn_info['conn_ip'] = host_info['ip']
            conn_info['conn_port'] = acc_info['protocol_port']

        conn_info['acc_id'] = acc_id
        conn_info['acc_username'] = acc_info['username']
        conn_info['username_prompt'] = ''
        conn_info['password_prompt'] = ''
        conn_info['protocol_flag'] = 1

        conn_info['protocol_type'] = acc_info['protocol_type']
        conn_info['protocol_sub_type'] = protocol_sub_type

        conn_info['auth_type'] = acc_info['auth_type']
        if acc_info['auth_type'] == TP_AUTH_TYPE_PASSWORD:
            conn_info['acc_secret'] = acc_info['password']
        elif acc_info['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY:
            conn_info['acc_secret'] = acc_info['pri_key']

        with tmp_conn_id_lock:
            global tmp_conn_id_base
            tmp_conn_id_base += 1
            conn_id = tmp_conn_id_base

        log.v(conn_info)
        tp_session().set('tmp-conn-info-{}'.format(conn_id), conn_info, 10)

        req = {'method': 'request_session', 'param': {'conn_id': conn_id}}
        _yr = core_service_async_post_http(req)
        _code, ret_data = yield _yr
        if _code != TPE_OK:
            return self.write_json(_code)
        if ret_data is None:
            return self.write_json(TPE_FAILED, '调用核心服务获取会话ID失败')

        if 'sid' not in ret_data:
            return self.write_json(TPE_FAILED, '核心服务获取会话ID时返回错误数据')

        data = dict()
        data['session_id'] = ret_data['sid']
        data['host_ip'] = host_info['ip']

        if conn_info['protocol_type'] == TP_PROTOCOL_TYPE_RDP:
            data['teleport_port'] = tp_cfg().core.rdp.port
        elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_SSH:
            data['teleport_port'] = tp_cfg().core.ssh.port
        elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_TELNET:
            data['teleport_port'] = tp_cfg().core.telnet.port

        return self.write_json(0, data=data)


class DoGetPoliciesHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
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
        sql_order['name'] = 'rank'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'state' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'search':
                    if len(_filter[i].strip()) == 0:
                        tmp.append(i)

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

            # _order = args['order']
            # if _order is not None:
            #     sql_order['name'] = _order['k']
            #     sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total, page_index, row_data = ops.get_policies(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoUpdatePolicyHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
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
            args['name'] = args['name'].strip()
            args['desc'] = args['desc'].strip()
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if len(args['name']) == 0:
            return self.write_json(TPE_PARAM)

        if args['id'] == -1:
            err, info = ops.create_policy(self, args)
        else:
            err = ops.update_policy(self, args)
            info = {}
        self.write_json(err, data=info)


class DoUpdatePoliciesHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
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
            p_ids = args['policy_ids']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if action == 'lock':
            err = ops.update_policies_state(self, p_ids, TP_STATE_DISABLED)
            return self.write_json(err)
        elif action == 'unlock':
            err = ops.update_policies_state(self, p_ids, TP_STATE_NORMAL)
            return self.write_json(err)
        elif action == 'remove':
            err = ops.remove_policies(self, p_ids)
            return self.write_json(err)
        else:
            return self.write_json(TPE_PARAM)


class DoAddMembersHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
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
            policy_id = int(args['policy_id'])
            policy_type = int(args['type'])
            ref_type = int(args['rtype'])
            members = args['members']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        err = ops.add_members(self, policy_id, policy_type, ref_type, members)
        self.write_json(err)


class DoRemoveMembersHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
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
            policy_id = int(args['policy_id'])
            policy_type = int(args['policy_type'])
            ids = args['ids']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        err = ops.remove_members(self, policy_id, policy_type, ids)
        self.write_json(err)


class DoSetFlagsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
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
            policy_id = int(args['policy_id'])
            flag_record = int(args['flag_record'])
            flag_rdp = int(args['flag_rdp'])
            flag_ssh = int(args['flag_ssh'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        err = ops.set_flags(self, policy_id, flag_record, flag_rdp, flag_ssh)
        self.write_json(err)


class DoGetOperatorsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        print('---get operator:', args)

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
                # if i == 'user_id' and _filter[i] == 0:
                #     tmp.append(i)
                #     continue
                if i == '_name':
                    if len(_filter[i].strip()) == 0:
                        tmp.append(i)

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

        err, total, page_index, row_data = ops.get_operators(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoGetAssetHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        print('---get asset:', args)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            # tmp = list()
            # _filter = args['filter']
            # for i in _filter:
            #     # if i == 'user_id' and _filter[i] == 0:
            #     #     tmp.append(i)
            #     #     continue
            #     if i == '_name':
            #         if len(_filter[i].strip()) == 0:
            #             tmp.append(i)
            #
            # for i in tmp:
            #     del _filter[i]

            sql_filter.update(args['filter'])

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

        err, total, page_index, row_data = ops.get_asset(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoRankReorderHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
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
            pid = int(args['pid'])
            new_rank = int(args['new_rank'])
            start_rank = int(args['start_rank'])
            end_rank = int(args['end_rank'])
            direct = int(args['direct'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if direct == -1:
            direct = '-1'
        elif direct == 1:
            direct = '+1'
        else:
            return self.write_json(TPE_PARAM)

        err = ops.rank_reorder(self, pid, new_rank, start_rank, end_rank, direct)
        self.write_json(err)


class DoGetRemotesHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS)
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
                # if i == 'user_id' and _filter[i] == 0:
                #     tmp.append(i)
                #     continue
                if i == '_name':
                    if len(_filter[i].strip()) == 0:
                        tmp.append(i)

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

        err, total, page_index, row_data = ops.get_remotes(self, sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoBuildAuzMapHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return

        err = ops.build_auz_map()
        self.write_json(err)
