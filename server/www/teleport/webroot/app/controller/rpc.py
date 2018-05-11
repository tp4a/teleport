# -*- coding: utf-8 -*-

import json
import urllib.parse

import tornado.gen
from app.const import *
from app.base.configs import tp_cfg
from app.base.session import tp_session
from app.base.core_server import core_service_async_post_http
from app.model import record
from app.base.stats import tp_stats
from app.base.logger import *
from app.base.controller import TPBaseJsonHandler


class RpcHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def get(self):
        _uri = self.request.uri.split('?', 1)
        if len(_uri) != 2:
            return self.write_json(TPE_PARAM)

        yield self._dispatch(urllib.parse.unquote(_uri[1]))

    @tornado.gen.coroutine
    def post(self):
        req = self.request.body.decode('utf-8')
        if req == '':
            return self.write_json(TPE_PARAM)

        yield self._dispatch(req)

    @tornado.gen.coroutine
    def _dispatch(self, req):
        try:
            _req = json.loads(req)

            if 'method' not in _req or 'param' not in _req:
                return self.write_json(TPE_PARAM)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        # log.d('WEB-JSON-RPC, method=`{}`\n'.format(_req['method']))

        if 'get_conn_info' == _req['method']:
            return self._get_conn_info(_req['param'])
        elif 'session_begin' == _req['method']:
            return self._session_begin(_req['param'])
        elif 'session_update' == _req['method']:
            return self._session_update(_req['param'])
        elif 'session_end' == _req['method']:
            return self._session_end(_req['param'])
        elif 'register_core' == _req['method']:
            return self._register_core(_req['param'])
        elif 'exit' == _req['method']:
            return self._exit()
        else:
            log.e('WEB-JSON-RPC got unknown method: `{}`.\n'.format(_req['method']))

        return self.write_json(TPE_UNKNOWN_CMD)

    def _get_conn_info(self, param):
        if 'conn_id' not in param:
            return self.write_json(TPE_PARAM)

        conn_id = param['conn_id']
        x = tp_session().taken('tmp-conn-info-{}'.format(conn_id), None)
        if x is None:
            return self.write_json(TPE_NOT_EXISTS)
        else:
            return self.write_json(TPE_OK, data=x)

    def _session_begin(self, param):
        try:
            _sid = param['sid']
            _user_id = param['user_id']
            _host_id = param['host_id']
            _account_id = param['acc_id']
            _user_name = param['user_username']
            _acc_name = param['acc_username']
            _host_ip = param['host_ip']
            _conn_ip = param['conn_ip']
            _conn_port = param['conn_port']
            _client_ip = param['client_ip']
            _auth_type = param['auth_type']
            _protocol_type = param['protocol_type']
            _protocol_sub_type = param['protocol_sub_type']
        except IndexError:
            return self.write_json(TPE_PARAM)

        err, record_id = record.session_begin(_sid, _user_id, _host_id, _account_id, _user_name, _acc_name, _host_ip, _conn_ip, _conn_port, _client_ip, _auth_type, _protocol_type, _protocol_sub_type)
        if err != TPE_OK:
            return self.write_json(err, message='can not write database.')
        else:
            tp_stats().conn_counter_change(1)
            return self.write_json(TPE_OK, data={'rid': record_id})

    def _session_update(self, param):
        try:
            rid = param['rid']
            protocol_sub_type = param['protocol_sub_type']
            code = param['code']
        except:
            return self.write_json(TPE_PARAM)
        if 'rid' not in param or 'code' not in param:
            return self.write_json(TPE_PARAM)

        if not record.session_update(rid, protocol_sub_type, code):
            return self.write_json(TPE_DATABASE, 'can not write database.')
        else:
            return self.write_json(TPE_OK)

    def _session_end(self, param):
        if 'rid' not in param or 'code' not in param:
            return self.write_json(TPE_PARAM, message='invalid request.')

        if not record.session_end(param['rid'], param['code']):
            return self.write_json(TPE_DATABASE, 'can not write database.')
        else:
            tp_stats().conn_counter_change(-1)
            return self.write_json(TPE_OK)

    def _register_core(self, param):
        # 因为core服务启动了（之前可能非正常终止了），做一下数据库中会话状态的修复操作
        record.session_fix()

        if 'rpc' not in param:
            return self.write_json(TPE_PARAM, 'invalid param.')

        tp_cfg().common.core_server_rpc = param['rpc']

        # 获取core服务的配置信息
        req = {'method': 'get_config', 'param': []}
        _yr = core_service_async_post_http(req)
        code, ret_data = yield _yr
        if code != TPE_OK:
            return self.write_json(code, 'get config from core-service failed.')

        log.d('update base server config info.\n')
        tp_cfg().update_core(ret_data)

        # 将运行时配置发送给核心服务
        req = {'method': 'set_config', 'param': {'noop_timeout': tp_cfg().sys.session.noop_timeout}}
        _yr = core_service_async_post_http(req)
        code, ret_data = yield _yr
        if code != TPE_OK:
            return self.write_json(code, 'set runtime-config to core-service failed.')

        return self.write_json(TPE_OK)

    def _exit(self):
        # set exit flag.
        return self.write_json(TPE_OK)
