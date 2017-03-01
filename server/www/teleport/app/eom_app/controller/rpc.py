# -*- coding: utf-8 -*-

import tornado.web
import tornado.gen

import json
import urllib.parse
from eom_app.module import host

from .base import SwxJsonHandler


class RpcHandler(SwxJsonHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        _uri = self.request.uri.split('?', 1)
        print(_uri)
        if len(_uri) != 2:
            self.write_json(-1, message='need request param.')
            return

        self._dispatch(urllib.parse.unquote(_uri[1]))

    def post(self):
        # curl -X POST --data '{"method":"get_auth_info","param":{"authid":0}}' http://127.0.0.1:7190/rpc
        req = self.request.body.decode('utf-8')
        if req == '':
            self.write_json(-1, message='need request param.')
            return

        self._dispatch(req)

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
        # todo: 如果是页面上进行连接测试（增加或修改主机和用户时），信息并不写入数据库，而是在内存中存在，传递给core服务的
        # 应该是随机字符串做authid，名称为 tauthid。本接口应该支持区分这两种认证ID。

        if 'authid' not in param:
            self.write_json(-1, message='invalid request.')
            return

        # 根据authid从数据库中查询对应的数据，然后返回给调用者
        x = host.get_auth_info(param['authid'])
        print('get_auth_info():', x)

        self.write_json(0, data=x)

    def _session_begin(self, param):
        if 'sid' not in param:
            self.write_json(-1, message='invalid request.')
            return

        self.write_json(0, data={'rid': 12})

    def _session_end(self, param):
        if 'rid' not in param or 'code' not in param:
            self.write_json(-1, message='invalid request.')
            return

        self.write_json(0)

    def _session_fix(self):
        # do db operation.
        self.write_json(0)

    def _exit(self):
        # set exit flag.
        self.write_json(0)
