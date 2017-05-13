# -*- coding: utf-8 -*-

import json
import urllib.parse

import tornado.gen
from eom_app.app.configs import app_cfg
from eom_app.app.session import web_session
from eom_app.app.util import async_post_http
from eom_app.module import host, record
from eom_common.eomcore.logger import *
from .base import TPBaseJsonHandler


class RpcHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def get(self):
        _uri = self.request.uri.split('?', 1)
        if len(_uri) != 2:
            return self.write_json(-1, message='need request param.')

        yield self._dispatch(urllib.parse.unquote(_uri[1]))

    @tornado.gen.coroutine
    def post(self):
        req = self.request.body.decode('utf-8')
        if req == '':
            return self.write_json(-1, message='need request param.')

        yield self._dispatch(req)

    @tornado.gen.coroutine
    def _dispatch(self, req):
        try:
            _req = json.loads(req)

            if 'method' not in _req or 'param' not in _req:
                return self.write_json(-1, message='invalid request format.')
        except:
            return self.write_json(-1, message='invalid json format.')

        if 'get_auth_info' == _req['method']:
            return self._get_auth_info(_req['param'])
        elif 'session_begin' == _req['method']:
            return self._session_begin(_req['param'])
        elif 'session_end' == _req['method']:
            return self._session_end(_req['param'])
        elif 'register_core' == _req['method']:
            return self._register_core(_req['param'])
        elif 'exit' == _req['method']:
            return self._exit()
        else:
            log.e('WEB-JSON-RPC got unknown method: `{}`.\n'.format(_req['method']))

        return self.write_json(-1, message='invalid method.')

    def _get_auth_info(self, param):
        # 如果是页面上进行连接测试（增加或修改主机和用户时），信息并不写入数据库，而是在内存中存在，传递给core服务的
        # 应该是负数形式的authid。本接口支持区分这两种认证ID。

        if 'authid' not in param:
            return self.write_json(-1, message='invalid request.')

        authid = param['authid']
        if authid > 0:
            # 根据authid从数据库中查询对应的数据，然后返回给调用者
            x = host.get_auth_info(param['authid'])
            return self.write_json(0, data=x)
        elif authid < 0:
            x = web_session().taken('tmp-auth-info-{}'.format(authid), None)
            return self.write_json(0, data=x)
        else:
            return self.write_json(-1, message='invalid auth id.')

    def _session_begin(self, param):
        if 'sid' not in param:
            return self.write_json(-1, message='invalid request.')

        try:
            _sid = param['sid']
            _acc_name = param['account_name']
            _host_ip = param['host_ip']
            _sys_type = param['sys_type']
            _host_port = param['host_port']
            _auth_mode = param['auth_mode']
            _user_name = param['user_name']
            _protocol = param['protocol']
        except IndexError:
            return self.write_json(-1, message='invalid request.')

        record_id = record.session_begin(_sid, _acc_name, _host_ip, _sys_type, _host_port, _auth_mode, _user_name, _protocol)
        if record_id <= 0:
            return self.write_json(-1, message='can not write database.')
        else:
            return self.write_json(0, data={'rid': record_id})

    def _session_end(self, param):
        if 'rid' not in param or 'code' not in param:
            return self.write_json(-1, message='invalid request.')

        if not record.session_end(param['rid'], param['code']):
            return self.write_json(-1, 'can not write database.')
        else:
            return self.write_json(0)

    def _register_core(self, param):
        # 因为core服务启动了（之前可能非正常终止了），做一下数据库中会话状态的修复操作
        record.session_fix()

        if 'rpc' not in param:
            return self.write_json(-1, 'invalid param.')

        app_cfg().core_server_rpc = param['rpc']

        # 获取core服务的配置信息
        req = {'method': 'get_config', 'param': []}
        _yr = async_post_http(req)
        return_data = yield _yr
        if return_data is None:
            return self.write_json(-1, 'get config from core service failed.')
        if 'code' not in return_data:
            return self.write_json(-2, 'get config from core service return invalid data.')
        if return_data['code'] != 0:
            return self.write_json(-3, 'get config from core service return code: {}'.format(return_data['code']))

        log.d('update core server config info.\n')
        app_cfg().update_core(return_data['data'])

        return self.write_json(0)

    def _exit(self):
        # set exit flag.
        return self.write_json(0)
