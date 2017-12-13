# -*- coding: utf-8 -*-

import json

import tornado.websocket
from app.base.session import tp_session
from app.base.wss import tp_wss
from app.const import *


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):  # 针对websocket处理类重写同源检查的方法
        return True

    # 接受websocket链接，保存链接实例
    def open(self, sid):
        # 处理新的连接
        k = '{}-{}'.format('user', sid)
        _user = tp_session().get(k, None)
        if _user is None:
            ret = {'code': TPE_NEED_LOGIN, 'message': '需要登录'}
            self.write_message(json.dumps(ret))
            return

        tp_wss().register(self)

    def on_close(self):
        if not tp_wss().have_callbacker(self):
            return
        tp_wss().unregister(self)  # 删除客户端连接

    def on_message(self, message):
        if not tp_wss().have_callbacker(self):
            ret = {'code': TPE_NEED_LOGIN, 'message': '未曾成功连接'}
            self.write_message(json.dumps(ret))
            return
        tp_wss().on_message(self, message)
