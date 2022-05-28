# -*- coding: utf-8 -*-

import json

import tornado.websocket
from tornado.escape import json_encode
from app.base.session import tp_session
from app.base.logger import *
from app.base.wss import tp_wss
from app.base.assist_bridge import tp_assist_bridge, AssistInfo, AssistMessage
from app.const import *


class DashboardHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):  # 针对websocket处理类重写同源检查的方法
        # print('ws-dashboard origin:', origin)
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


class AssistHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.client_type: int = AssistInfo.WS_CLIENT_UNKNOWN
        self.assist_id: int = 0
        self.close()

    def check_origin(self, origin):  # 针对websocket处理类重写同源检查的方法
        return True

    def send_request(self, msg: AssistMessage, param=None):
        if param is None:
            param = {}
        data = {
            'type': AssistMessage.MESSAGE_TYPE_REQUEST,
            'command_id': msg.cmd_id,
            'method': msg.method,
            'param': param
        }
        log.d('send ws request: {}\n'.format(json_encode(data)))
        self.write_message(json_encode(data))

    def send_response(self, msg: AssistMessage, code, message='', data=None):
        if data is None:
            data = {}
        ret = {
            'type': AssistMessage.MESSAGE_TYPE_RESPONSE,
            'command_id': msg.cmd_id,
            'method': msg.method,
            'code': code,
            'message': message,
            'data': data
        }
        log.d('send ws response: {}\n'.format(json_encode(ret)))
        self.write_message(json_encode(ret))

    def set_assist_id(self, assist_id: int) -> None:
        self.assist_id = assist_id

    def open(self, message):
        log.w('message on_open: {}\n'.format(message))
        self.on_message(message)

    def on_close(self):
        tp_assist_bridge().on_disconnect(self)

    def on_message(self, message):
        if message == 'PING':
            return self.write_message('PONG')

        log.d('raw on_message: {}\n'.format(message))

        msg_req = AssistMessage(self, 'UNKNOWN')

        try:
            msg = json.loads(message)
        except Exception as e:
            log.e('need json format: {}\n'.format(e.__str__()))
            return self.send_response(msg_req, TPE_JSON_FORMAT)

        if 'type' not in msg:
            log.e('need `type` fields: {}\n'.format(message))
            return self.send_response(msg_req, TPE_PARAM)

        if 'method' not in msg:
            log.e('need `method` fields: {}\n'.format(message))
            return self.send_response(msg_req, TPE_PARAM)
        msg_req.method = msg['method']

        if msg['type'] == AssistMessage.MESSAGE_TYPE_REQUEST:
            param = msg['param'] if 'param' in msg else None

            if msg['method'] == 'register':
                if param is None:
                    log.e('need `param` field: {}\n'.format(message))
                    return self.send_response(msg_req, TPE_PARAM)

                if 'client' not in param:
                    log.e('need `client` field: {}\n'.format(message))
                    return self.send_response(msg_req, TPE_PARAM)

                if param['client'] == 'web':
                    self.client_type = AssistInfo.WS_CLIENT_WEB
                    self._on_web_client_connected(msg_req, param)
                elif param['client'] == 'assist':
                    self.client_type = AssistInfo.WS_CLIENT_ASSIST
                    tp_assist_bridge().on_assist_connect(msg_req, param)
                else:
                    log.e('未知的客户端类型：{}\n'.format(msg['client']))
                    return self.send_response(msg_req, TPE_PARAM)

            else:
                tp_assist_bridge().on_request(msg_req, param)

        elif msg['type'] == AssistMessage.MESSAGE_TYPE_RESPONSE:
            if 'command_id' not in msg or msg['command_id'] == 0:
                log.e('invalid response, need `command_id`: {}\n'.format(message))
                return
            log.d('forward: {}\n'.format(message))
            tp_assist_bridge().forward_response(self, msg)
        else:
            log.e('unknown `type` field in message: {}\n'.format(message))
            return self.send_response(msg_req, TPE_PARAM)

    def _on_web_client_connected(self, msg_req, param):
        s_id = self.get_cookie('_sid')
        if s_id is None:
            return self.send_response(msg_req, TPE_NEED_LOGIN, '需要登录')

        k = 'user-{}'.format(s_id)
        user_info = tp_session().get(k, None)
        if user_info is None or not user_info['_is_login']:
            return self.send_response(msg_req, TPE_NEED_LOGIN, '需要登录')

        tp_assist_bridge().on_web_client_connect(msg_req, s_id, param)
