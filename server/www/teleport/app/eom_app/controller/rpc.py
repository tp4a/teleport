# -*- coding: utf-8 -*-

# import tornado.web
import tornado.gen

import json
import urllib.parse
from eom_app.app.session import web_session
from eom_app.module import host, record

from .base import SwxJsonHandler


class RpcHandler(SwxJsonHandler):
    @tornado.gen.coroutine
    def get(self):
        _uri = self.request.uri.split('?', 1)
        print(_uri)
        if len(_uri) != 2:
            self.write_json(-1, message='need request param.')
            return

        yield self._dispatch(urllib.parse.unquote(_uri[1]))

    @tornado.gen.coroutine
    def post(self):
        # curl -X POST --data '{"method":"get_auth_info","param":{"authid":0}}' http://127.0.0.1:7190/rpc
        req = self.request.body.decode('utf-8')
        if req == '':
            self.write_json(-1, message='need request param.')
            return

        yield self._dispatch(req)

    @tornado.gen.coroutine
    def _dispatch(self, req):
        print('rpc-req:', req)
        try:
            _req = json.loads(req)

            if 'method' not in _req or 'param' not in _req:
                self.write_json(-1, message='invalid request format.')
                return

        except:
            self.write_json(-1, message='invalid json format.')
            return

        if 'get_auth_info' == _req['method']:
            return self._get_auth_info(_req['param'])
        elif 'session_begin' == _req['method']:
            return self._session_begin(_req['param'])
        elif 'session_end' == _req['method']:
            return self._session_end(_req['param'])
        elif 'session_fix' == _req['method']:
            return self._session_fix()
        elif 'exit' == _req['method']:
            return self._exit()

        self.write_json(-1, message='invalid method.')

    def _get_auth_info(self, param):
        # 如果是页面上进行连接测试（增加或修改主机和用户时），信息并不写入数据库，而是在内存中存在，传递给core服务的
        # 应该是负数形式的authid。本接口支持区分这两种认证ID。

        if 'authid' not in param:
            self.write_json(-1, message='invalid request.')
            return

        authid = param['authid']
        if authid > 0:
            # 根据authid从数据库中查询对应的数据，然后返回给调用者
            x = host.get_auth_info(param['authid'])
            print('get_auth_info():', x)
            self.write_json(0, data=x)
        elif authid < 0:
            x = web_session().taken('tmp-auth-info-{}'.format(authid), None)
            print('get_auth_info():', x)
            self.write_json(0, data=x)
        else:
            self.write_json(-1, message='invalid auth id.')

    def _session_begin(self, param):
        if 'sid' not in param:
            return self.write_json(-1, message='invalid request.')

        # jreq["param"]["sid"] = info.sid.c_str();
        # jreq["param"]["account_name"] = info.account_name.c_str();
        # jreq["param"]["host_ip"] = info.host_ip.c_str();
        # jreq["param"]["sys_type"] = info.sys_type;
        # jreq["param"]["host_port"] = info.host_port;
        # jreq["param"]["auth_mode"] = info.auth_mode,
        # jreq["param"]["user_name"] = info.user_name.c_str();
        # jreq["param"]["protocol"] = info.protocol;

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
            self.write_json(-1, message='can not write database.')
        else:
            self.write_json(0, data={'rid': record_id})

    def _session_end(self, param):
        if 'rid' not in param or 'code' not in param:
            self.write_json(-1, message='invalid request.')
            return

        if not record.session_end(param['rid'], param['code']):
            self.write_json(-1)
        else:
            self.write_json(0)

    def _session_fix(self):
        record.session_fix()
        self.write_json(0)

    def _exit(self):
        # set exit flag.
        self.write_json(0)
