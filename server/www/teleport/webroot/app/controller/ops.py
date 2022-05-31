# -*- coding: utf-8 -*-

import json
import threading
import time
from copy import deepcopy

import tornado.httpclient
import tornado.gen
from app.base.logger import log
from app.base.configs import tp_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.core_server import *
from app.base.session import tp_session
from app.base.utils import tp_unique_id, tp_timestamp_sec
from app.const import *
from app.model import account
from app.model import host
from app.model import ops
from app.model import group
from ._sidebar_menu import tp_generate_sidebar


class AuzListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return
        self.render('ops/auz-list.html', sidebar_menu=tp_generate_sidebar(self))


class RemoteHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS)
        if ret != TPE_OK:
            return

        core_cfg = deepcopy(tp_cfg().core)
        del core_cfg['replay_path']
        del core_cfg['web_server_rpc']

        err, groups = group.get_host_groups_for_user(self.current_user['id'], self.current_user['privilege'])
        param = {
            'host_groups': groups,
            'core_cfg': core_cfg
        }

        # param = {
        #     'core_cfg': tp_cfg().core
        # }

        self.render('ops/remote-list.html', page_param=json.dumps(param), sidebar_menu=tp_generate_sidebar(self))


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
        self.render('ops/auz-info.html', page_param=json.dumps(param), sidebar_menu=tp_generate_sidebar(self))


class SessionListsHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return
        self.render('ops/sessions.html', sidebar_menu=tp_generate_sidebar(self))


@tornado.gen.coroutine
def api_request_session_id(acc_id, protocol_sub_type, client_ip, operator, privilege):
    ret = {
        'code': TPE_OK,
        'message': '',
        'data': {}
    }

    # 检查权限
    if (privilege & TP_PRIVILEGE_OPS) == 0:
        ret['code'] = TPE_PRIVILEGE
        ret['message'] = '权限不足'
        return ret

    conn_info = dict()
    conn_info['_enc'] = 1
    conn_info['host_id'] = 0
    conn_info['client_ip'] = client_ip
    conn_info['user_id'] = 1
    conn_info['user_username'] = operator

    err, acc_info = account.get_account_info(acc_id)
    if err != TPE_OK:
        ret['code'] = err
        ret['message'] = '无此远程账号'
        return ret

    host_id = acc_info['host_id']
    acc_info['protocol_flag'] = TP_FLAG_ALL
    acc_info['record_flag'] = TP_FLAG_ALL

    # 获取要远程连接的主机信息（要访问的IP地址，如果是路由模式，则是路由主机的IP+端口）
    err, host_info = host.get_host_info(host_id)
    if err != TPE_OK:
        ret['code'] = err
        ret['message'] = '未找到对应远程主机'
        return ret

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
    conn_info['username_prompt'] = acc_info['username_prompt']
    conn_info['password_prompt'] = acc_info['password_prompt']
    conn_info['protocol_flag'] = acc_info['protocol_flag']
    conn_info['record_flag'] = acc_info['record_flag']

    conn_info['protocol_type'] = acc_info['protocol_type']
    conn_info['protocol_sub_type'] = protocol_sub_type

    conn_info['auth_type'] = acc_info['auth_type']
    if acc_info['auth_type'] == TP_AUTH_TYPE_PASSWORD:
        conn_info['acc_secret'] = acc_info['password']
    elif acc_info['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY:
        conn_info['acc_secret'] = acc_info['pri_key']
    else:
        conn_info['acc_secret'] = ''

    conn_id = tp_unique_id()

    # log.v('CONN-INFO:', conn_info)
    tp_session().set('tmp-conn-info-{}'.format(conn_id), conn_info, 10)

    req = {'method': 'request_session', 'param': {'conn_id': conn_id}}
    _yr = core_service_async_post_http(req)
    _code, ret_data = yield _yr
    if _code != TPE_OK:
        ret['code'] = _code
        ret['message'] = '无法连接到核心服务'
        return ret
    if ret_data is None:
        ret['code'] = TPE_FAILED
        ret['message'] = '调用核心服务获取会话ID失败'
        return ret

    if 'sid' not in ret_data:
        ret['code'] = TPE_FAILED
        ret['message'] = '核心服务获取会话ID时返回错误数据'
        return ret

    data = dict()
    data['session_id'] = ret_data['sid']
    data['host_ip'] = host_info['ip']
    data['host_name'] = host_info['name']
    data['protocol_flag'] = acc_info['protocol_flag']

    if conn_info['protocol_type'] == TP_PROTOCOL_TYPE_RDP:
        data['teleport_port'] = tp_cfg().core.rdp.port
    elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_SSH:
        data['teleport_port'] = tp_cfg().core.ssh.port
    elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_TELNET:
        data['teleport_port'] = tp_cfg().core.telnet.port

    ret['code'] = TPE_OK
    ret['message'] = ''
    ret['data'] = data
    return ret


@tornado.gen.coroutine
def api_v2_request_session_id(
        remote_ip, remote_port, remote_auth_type, remote_user, remote_secret,
        protocol_type, protocol_sub_type, client_ip, operator, privilege):
    ret = {
        'code': TPE_OK,
        'message': '',
        'data': {}
    }

    # 检查权限
    if (privilege & TP_PRIVILEGE_OPS) == 0:
        ret['code'] = TPE_PRIVILEGE
        ret['message'] = '权限不足'
        return ret

    conn_info = dict()
    conn_info['_enc'] = 0
    conn_info['host_id'] = 0
    conn_info['client_ip'] = client_ip
    conn_info['user_id'] = 0
    conn_info['user_username'] = operator

    conn_info['host_ip'] = remote_ip
    conn_info['conn_ip'] = remote_ip
    conn_info['conn_port'] = remote_port

    conn_info['acc_id'] = 0
    conn_info['acc_username'] = remote_user
    conn_info['username_prompt'] = ''
    conn_info['password_prompt'] = ''
    conn_info['protocol_flag'] = TP_FLAG_ALL
    conn_info['record_flag'] = TP_FLAG_ALL

    conn_info['protocol_type'] = protocol_type
    conn_info['protocol_sub_type'] = protocol_sub_type

    conn_info['auth_type'] = remote_auth_type
    conn_info['acc_secret'] = remote_secret

    conn_id = tp_unique_id()

    # log.v('CONN-INFO:', conn_info)
    tp_session().set('tmp-conn-info-{}'.format(conn_id), conn_info, 10)

    req = {'method': 'request_session', 'param': {'conn_id': conn_id}}
    _yr = core_service_async_post_http(req)
    _code, ret_data = yield _yr
    if _code != TPE_OK:
        ret['code'] = _code
        ret['message'] = '无法连接到核心服务'
        return ret
    if ret_data is None:
        ret['code'] = TPE_FAILED
        ret['message'] = '调用核心服务获取会话ID失败'
        return ret

    if 'sid' not in ret_data:
        ret['code'] = TPE_FAILED
        ret['message'] = '核心服务获取会话ID时返回错误数据'
        return ret

    data = dict()
    data['session_id'] = ret_data['sid']
    data['host_ip'] = remote_ip
    data['host_name'] = ''
    data['protocol_flag'] = TP_FLAG_ALL

    if conn_info['protocol_type'] == TP_PROTOCOL_TYPE_RDP:
        data['teleport_port'] = tp_cfg().core.rdp.port
    elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_SSH:
        data['teleport_port'] = tp_cfg().core.ssh.port
    elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_TELNET:
        data['teleport_port'] = tp_cfg().core.telnet.port

    ret['code'] = TPE_OK
    ret['message'] = ''
    ret['data'] = data
    return ret


class DoGetSessionIDHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        # ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_OPS | TP_PRIVILEGE_OPS_AUZ)
        # if ret != TPE_OK:
        #     return

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

        try:
            _mode = int(args['mode'])
            _protocol_type = int(args['protocol_type'])
            _protocol_sub_type = int(args['protocol_sub_type'])
        except:
            return self.write_json(TPE_PARAM)

        conn_info = dict()
        conn_info['_enc'] = 1
        conn_info['host_id'] = 0
        conn_info['client_ip'] = self.request.remote_ip
        conn_info['user_id'] = self.get_current_user()['id']
        conn_info['user_username'] = self.get_current_user()['username']

        # mode = 0:  test connect
        # mode = 1:  user connect
        # mode = 2:  admin connect
        if _mode == 1:
            # 通过指定的auth_id连接（需要授权），必须具有远程运维的权限方可进行
            ret = self.check_privilege(TP_PRIVILEGE_OPS)
            if ret != TPE_OK:
                return

            if 'auth_id' not in args or 'protocol_sub_type' not in args:
                return self.write_json(TPE_PARAM)

            # 根据auth_id从数据库中取得此授权相关的用户、主机、账号三者详细信息
            auth_id = args['auth_id']
            ops_auth, err = ops.get_auth(auth_id)
            if err != TPE_OK:
                return self.write_json(err)

            if ops_auth['u_id'] != self._user['id']:
                return self.write_json(TPE_PRIVILEGE)

            policy_id = ops_auth['p_id']
            acc_id = ops_auth['a_id']
            host_id = ops_auth['h_id']

            err, policy_info = ops.get_by_id(policy_id)
            if err != TPE_OK:
                return self.write_json(err)

            err, acc_info = account.get_account_info(acc_id)
            if err != TPE_OK:
                return self.write_json(err)
            # log.v(acc_info)

            if acc_info['protocol_type'] == TP_PROTOCOL_TYPE_RDP:
                acc_info['protocol_flag'] = policy_info['flag_rdp']
            elif acc_info['protocol_type'] == TP_PROTOCOL_TYPE_SSH:
                acc_info['protocol_flag'] = policy_info['flag_ssh']
            elif acc_info['protocol_type'] == TP_PROTOCOL_TYPE_TELNET:
                acc_info['protocol_flag'] = policy_info['flag_telnet']
            else:
                acc_info['protocol_flag'] = 0
            acc_info['record_flag'] = policy_info['flag_record']

        elif _mode == 2:
            # 直接连接（无需授权），必须具有运维授权管理的权限方可进行
            ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
            if ret != TPE_OK:
                return

            acc_id = args['acc_id']

            err, acc_info = account.get_account_info(acc_id)
            if err != TPE_OK:
                return self.write_json(err)

            host_id = acc_info['host_id']
            acc_info['protocol_flag'] = TP_FLAG_ALL
            acc_info['record_flag'] = TP_FLAG_ALL

        elif _mode == 0:
            # 测试连接，必须具有主机信息创建、编辑的权限方可进行
            ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE)
            if ret != TPE_OK:
                return

            conn_info['_test'] = 1
            try:
                acc_id = int(args['acc_id'])
                host_id = int(args['host_id'])
                auth_type = int(args['auth_type'])
                username = args['username']
                password = args['password']
                pri_key = args['pri_key']
                protocol_port = int(args['protocol_port'])
                username_prompt = args['username_prompt']
                password_prompt = args['password_prompt']
            except:
                return self.write_json(TPE_PARAM)

            if len(username) == 0:
                return self.write_json(TPE_PARAM)

            acc_info = dict()

            acc_info['auth_type'] = auth_type
            acc_info['protocol_type'] = _protocol_type
            acc_info['protocol_port'] = protocol_port
            acc_info['protocol_flag'] = TP_FLAG_ALL
            acc_info['record_flag'] = TP_FLAG_ALL
            acc_info['username'] = username

            acc_info['password'] = password
            acc_info['pri_key'] = pri_key

            acc_info['username_prompt'] = username_prompt
            acc_info['password_prompt'] = password_prompt

            conn_info['_enc'] = 0

            if acc_id == -1:
                # if auth_type == TP_AUTH_TYPE_PASSWORD and len(password) == 0:
                #     return self.write_json(TPE_PARAM)
                if auth_type == TP_AUTH_TYPE_PRIVATE_KEY and len(pri_key) == 0:
                    return self.write_json(TPE_PARAM)
            else:
                if (auth_type == TP_AUTH_TYPE_PASSWORD and len(password) == 0) or (auth_type == TP_AUTH_TYPE_PRIVATE_KEY and len(pri_key) == 0):
                    err, _acc_info = account.get_account_info(acc_id)
                    if err != TPE_OK:
                        return self.write_json(err)
                    acc_info['password'] = _acc_info['password']
                    acc_info['pri_key'] = _acc_info['pri_key']

                    conn_info['_enc'] = 1

        else:
            return self.write_json(TPE_PARAM)

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
        conn_info['username_prompt'] = acc_info['username_prompt']
        conn_info['password_prompt'] = acc_info['password_prompt']
        conn_info['protocol_flag'] = acc_info['protocol_flag']
        conn_info['record_flag'] = acc_info['record_flag']

        conn_info['protocol_type'] = acc_info['protocol_type']
        conn_info['protocol_sub_type'] = _protocol_sub_type

        conn_info['auth_type'] = acc_info['auth_type']
        if acc_info['auth_type'] == TP_AUTH_TYPE_PASSWORD:
            conn_info['acc_secret'] = acc_info['password']
        elif acc_info['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY:
            conn_info['acc_secret'] = acc_info['pri_key']
        else:
            conn_info['acc_secret'] = ''

        conn_id = tp_unique_id()

        # log.v('CONN-INFO:', conn_info)
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
        data['host_name'] = host_info['name']
        data['protocol_flag'] = acc_info['protocol_flag']

        if conn_info['protocol_type'] == TP_PROTOCOL_TYPE_RDP:
            data['teleport_port'] = tp_cfg().core.rdp.port
        elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_SSH:
            data['teleport_port'] = tp_cfg().core.ssh.port
        elif conn_info['protocol_type'] == TP_PROTOCOL_TYPE_TELNET:
            data['teleport_port'] = tp_cfg().core.telnet.port

        return self.write_json(TPE_OK, data=data)


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

        # print('---get operator:', args)

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

        # print('---get asset:', args)

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
        ret = self.check_privilege(TP_PRIVILEGE_OPS | TP_PRIVILEGE_OPS_AUZ)
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
                if i == 'search':
                    if len(_filter[i].strip()) == 0:
                        tmp.append(i)
                    continue
                elif i == 'host_group':
                    if _filter[i] == -1:
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

        err, total, page_index, row_data = ops.get_remotes(self, sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoKillSessionsHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
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
            sessions = args['sessions']
        except:
            return self.write_json(TPE_PARAM)

        req = {'method': 'kill_sessions', 'param': {'sessions': sessions}}
        _yr = core_service_async_post_http(req)
        _err, _ = yield _yr
        self.write_json(_err)


class DoBuildAuzMapHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ)
        if ret != TPE_OK:
            return

        err = ops.build_auz_map()
        self.write_json(err)


class DoGetOpsTokensHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
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

        try:
            uni_id = args['uni_id']
            acc_id = int(args['acc_id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        user_id = self.current_user['id']

        err, password = account.get_account_password(acc_id)
        if err != TPE_OK:
            return self.write_json(err)
        is_interactive = True if len(password) == 0 else False

        err, ret = ops.get_ops_tokens_by_user_and_acc(uni_id, user_id, acc_id)
        if err != TPE_OK:
            return self.write_json(err)

        for item in ret:
            item['_interactive'] = is_interactive
        self.write_json(TPE_OK, data=ret)


class DoCreateOpsTokenHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
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

        try:
            mode = args['mode']
            uni_id = args['uni_id']
            acc_id = int(args['acc_id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        # mode=TP_OPS_TOKEN_USER, 创建一个用户使用的授权码（远程连接时需要知道用户的密码）
        # mode=TP_OPS_TOKEN_TEMP, 创建一个临时使用的授权码（会返回授权码对应的认证密码，无需知道用户的密码）
        valid_from = tp_timestamp_sec()
        if mode == TP_OPS_TOKEN_USER:
            valid_to = valid_from + 90 * 24 * 60 * 60
        elif mode == TP_OPS_TOKEN_TEMP:
            valid_to = valid_from + 24 * 60 * 60
        else:
            return self.write_json(TPE_PARAM)

        err, password = account.get_account_password(acc_id)
        if err != TPE_OK:
            return self.write_json(err)
        is_interactive = True if len(password) == 0 else False

        err, token_info, temp_password = ops.create_ops_token(self, mode, uni_id, acc_id, valid_from, valid_to)
        if err != TPE_OK:
            return self.write_json(err)

        token_info['_interactive'] = is_interactive
        if mode == TP_OPS_TOKEN_TEMP:
            token_info['_password'] = temp_password
        self.write_json(TPE_OK, data=token_info)


class DoRemoveOpsTokenHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
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

        try:
            token = args['token']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        err = ops.remove_ops_token(self, token)
        self.write_json(err)


class DoRenewOpsTokenHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
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

        try:
            mode = args['mode']
            token = args['token']
            acc_id = int(args['acc_id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        now = tp_timestamp_sec()
        if mode == TP_OPS_TOKEN_USER:
            valid_to = now + 90 * 24 * 60 * 60
        elif mode == TP_OPS_TOKEN_TEMP:
            valid_to = now + 24 * 60 * 60
        else:
            return self.write_json(TPE_PARAM)

        err, password = account.get_account_password(acc_id)
        if err != TPE_OK:
            return self.write_json(err)
        is_interactive = True if len(password) == 0 else False

        err, token_info = ops.renew_ops_token(self, mode, token, acc_id, valid_to)
        token_info['_interactive'] = is_interactive
        self.write_json(err, data=token_info)


class DoCreateOpsTokenTempPasswordHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
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

        try:
            token = args['token']
            acc_id = int(args['acc_id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        err, password = account.get_account_password(acc_id)
        if err != TPE_OK:
            return self.write_json(err)
        is_interactive = True if len(password) == 0 else False

        err, token_info, temp_password = ops.create_ops_token_temp_password(self, token, acc_id)
        token_info['_interactive'] = is_interactive
        token_info['_password'] = temp_password
        self.write_json(err, data=token_info)
