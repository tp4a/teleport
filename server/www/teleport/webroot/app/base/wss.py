# -*- coding: utf-8 -*-

import json
import threading

from app.base.logger import *


class TPWebSocketServer(object):
    _clients = {}
    _lock = threading.RLock()

    def __init__(self):
        super().__init__()

        import builtins
        if '__tp_websocket_server__' in builtins.__dict__:
            raise RuntimeError('TPWebSocketServer object exists, you can not create more than one instance.')

        self._cb_get_sys_status = None
        self._cb_get_stat_counter = None

    def register_get_sys_status_callback(self, cb):
        self._cb_get_sys_status = cb

    def register_get_stat_counter_callback(self, cb):
        self._cb_get_stat_counter = cb

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
        # print('got message', message)
        try:
            req = json.loads(message)
        except:
            log.e('need json-format request.\n')
            return

        if req['method'] == 'subscribe':
            for p in req['params']:
                if p not in self._clients[callbacker]['subscribe']:
                    self._clients[callbacker]['subscribe'].append(p)
        elif req['method'] == 'request':
            if req['param'] == 'sys_status':
                if self._cb_get_sys_status is not None:
                    message = self._cb_get_sys_status()
                    msg = {'method': 'request', 'param': 'sys_status', 'data': message}
                    s = json.dumps(msg, separators=(',', ':'))
                    callbacker.write_message(s)
            if req['param'] == 'stat_counter':
                if self._cb_get_stat_counter is not None:
                    message = self._cb_get_stat_counter()
                    msg = {'method': 'request', 'param': 'stat_counter', 'data': message}
                    s = json.dumps(msg, separators=(',', ':'))
                    callbacker.write_message(s)

    def send_message(self, subscribe, message):
        s = None
        with self._lock:
            for c in self._clients:
                if subscribe in self._clients[c]['subscribe']:
                    if s is None:
                        msg = {'method': 'subscribe', 'param': subscribe, 'data': message}
                        s = json.dumps(msg, separators=(',', ':'))
                    c.write_message(s)


def tp_wss():
    """
    取得 TPWebSocketServer 管理器的唯一实例

    :rtype : TPWebSocketServer
    """

    import builtins
    if '__tp_websocket_server__' not in builtins.__dict__:
        builtins.__dict__['__tp_websocket_server__'] = TPWebSocketServer()
    return builtins.__dict__['__tp_websocket_server__']
