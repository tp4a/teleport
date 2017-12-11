# -*- coding: utf-8 -*-

import json
# import urllib.parse
import threading

# import tornado.gen
from app.const import *
# from app.base.configs import tp_cfg
from app.base.session import tp_session
# from app.base.core_server import core_service_async_post_http
# from app.model import record
from app.base.logger import *
# from app.base.controller import TPBaseJsonHandler
import tornado.websocket


class TPWebSocketServer(object):
    _clients = {}
    _lock = threading.RLock()

    def __init__(self):
        super().__init__()

        import builtins
        if '__tp_websocket_server__' in builtins.__dict__:
            raise RuntimeError('TPWebSocketServer object exists, you can not create more than one instance.')

    def have_callbacker(self, callbacker):
        return callbacker in self._clients

    def register(self, callbacker):
        # 记录客户端连接实例
        with self._lock:
            if not self.have_callbacker(callbacker):
                self._clients[callbacker] = {'subscribe': []}

    def unregister(self, callbacker):
        with self._lock:
            # 删除客户端连接实例
            try:
                del self._clients[callbacker]
            except:
                # print('when unregister, not exists.')
                pass

    def on_message(self, callbacker, message):
        print('got message', message)
        try:
            req = json.loads(message)
        except:
            log.e('need json-format request.\n')
            return

        if req['method'] == 'subscribe':
            for p in req['params']:
                if p not in self._clients[callbacker]['subscribe']:
                    self._clients[callbacker]['subscribe'].append(p)

    def send_message(self, subscribe, message):
        msg = {'subscribe': subscribe, 'data': message}
        s = json.dumps(msg, separators=(',', ':'))
        with self._lock:
            for c in self._clients:

                if subscribe in self._clients[c]['subscribe']:
                    c.write_message(s)

    # def response(self, _id, data):
    #     # print('send to client:', url, data)
    #     for callbacker in self.clients:
    #         if self.clients[callbacker].get_id() == _id:
    #             print('[ws] response', _id, data)
    #             callbacker.write_message(data)
    #             return
    #     print('## [ws] response no client.', _id)


def tp_wss():
    """
    取得 TPWebSocketServer 管理器的唯一实例

    :rtype : TPWebSocketServer
    """

    import builtins
    if '__tp_websocket_server__' not in builtins.__dict__:
        builtins.__dict__['__tp_websocket_server__'] = TPWebSocketServer()
    return builtins.__dict__['__tp_websocket_server__']


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):  # 针对websocket处理类重写同源检查的方法
        # print('check_origin: ', origin)
        return True

    # 接受websocket链接，保存链接实例
    def open(self, sid):
        # 处理新的连接
        k = '{}-{}'.format('user', sid)
        _user = tp_session().get(k, None)
        print(_user)
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

