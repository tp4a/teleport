# -*- coding: utf-8 -*-

from typing import Optional, Dict
import json
import threading

# import app.controller.ws
from app.const import *
from app.base.utils import tp_unique_id, tp_timestamp_sec
from app.base.logger import *


# 页面多个session-id可能对应同一个助手实例
# assist attributes:
#   - assist_id
#   - assist_ws_client    助手的ws连接
#   - last_transfer_time  最后一次通讯时间（用于超时断开助手的ws连接）[此功能可选]


# 命令请求/响应的格式：
# request
# {"type": 0, "method": "METHOD, like register", "command_id": 1234, "param": {} }
# response
# {"type": 1, "code" 0, "message": "", "method": "METHOD", "command_id": 1234, "data": {} }


class AssistMessage(object):
    """request/response between web-ws-client and assist-ws-client.
    """

    MESSAGE_TYPE_REQUEST = 0
    MESSAGE_TYPE_RESPONSE = 1

    def __init__(self, caller, method):
        super().__init__()

        # 命令的全局唯一id
        self.cmd_id: int = tp_unique_id()
        self.method: str = method
        # 命令发送给被调用端时的时间戳，错过一定时间未完结的命令，将会被扔掉
        self.start_time: int = tp_timestamp_sec()
        # self.caller: app.controller.ws.AssistHandler = caller
        # self.callee: Optional[app.controller.ws.AssistHandler] = None
        self.caller = caller
        self.callee = None

    def send_request(self, callee, param=None):
        self.callee = callee
        #
        tp_assist_bridge().handle_assist_message(self)

        self.callee.send_request(self, param)


class AssistInfo(object):
    WS_CLIENT_UNKNOWN = 0
    WS_CLIENT_WEB = 1
    WS_CLIENT_ASSIST = 2

    def __init__(self):
        super().__init__()

        self.assist_id = 0
        self.assist_ver = ''
        self.assist_ws = None


class TPAssistBridge(object):
    def __init__(self):
        super().__init__()

        import builtins
        if '__tp_assist_bridge__' in builtins.__dict__:
            raise RuntimeError('TPAssistBridge object exists, you can not create more than one instance.')

        self._lock = threading.RLock()

        # 会话ID对应的助手ID，多对一
        # SESSION-ID --> assist-id
        self._sid_to_assist = dict()

        # 助手ID对应的助手信息，一对一
        # assist_id --> AssistInfo
        self._assists = dict()

        # 页面会话的ws客户端连接
        # AssistHandler  -->  assist-id
        self._ws_web = dict()

        # 助手会话的ws客户端连接
        # AssistHandler  -->  assist-id
        self._ws_assist = dict()

        # 未完结的命令
        self._commands: Dict[int, AssistMessage] = dict()

    def finalize(self):
        # stop all websocket when stop web-server.
        with self._lock:
            for caller in self._ws_web:
                caller.close()

    def get_assist_bridge(self, s_id):
        with self._lock:
            assist_id = self._sid_to_assist[s_id] if s_id in self._sid_to_assist else 0
            if assist_id == 0:
                return None
            assist_info = self._assists[assist_id] if assist_id in self._assists else None
            return assist_info

    def handle_assist_message(self, msg_req: AssistMessage):
        # log.v('add message, cmd_id={}\n'.format(msg_req.cmd_id))
        self._commands[msg_req.cmd_id] = msg_req

    def on_web_client_connect(self, msg_req: AssistMessage, s_id: str, param: dict) -> None:
        with self._lock:
            assist_id = self._sid_to_assist[s_id] if s_id in self._sid_to_assist else 0
            if assist_id != 0:
                assist_info = self._assists[assist_id] if assist_id in self._assists else None
                if assist_info is not None:
                    self._ws_web[msg_req.caller] = assist_id
                    msg_req.caller.set_assist_id(assist_id)

                    assist_msg = AssistMessage(msg_req.caller, 'update_assist_info')
                    msg_param = {'assist_id': assist_id, 'assist_ver': assist_info.assist_ver}
                    msg_req.caller.send_response(assist_msg, TPE_OK, data=msg_param)

                    if 'exec' in param:
                        exec_param = param['exec']
                        assist_msg = AssistMessage(msg_req.caller, exec_param['method'])
                        msg_param = exec_param['param']
                        # assist_info.assist_ws.send_request(assist_msg, msg_param)
                        assist_msg.send_request(assist_info.assist_ws, msg_param)

                    return
                else:
                    del self._sid_to_assist[s_id]

            # 页面登录后首次连接此ws，此时当前会话还没有对应的助手ws，因此返回一个 request_assist_id，让页面通过url-protocol
            # 的方式调起助手。但是助手有可能已经在别的会话中存在ws连接，并且有另外的assist_id，因此助手会回一个正确的assist_id，
            # 然后才能完成 assist_id 与 web页面的绑定。
            assist_id = tp_unique_id()
            log.w('ws-web connected, but no assist bind, try to bind assist-id: {}\n'.format(assist_id))
            self._ws_web[msg_req.caller] = assist_id
            msg_req.caller.set_assist_id(assist_id)
            assist_msg = AssistMessage(msg_req.caller, 'start_assist')
            msg_param = {'request_assist_id': assist_id}
            if 'exec' in param:
                msg_param['exec'] = param['exec']
            msg_req.caller.send_response(assist_msg, TPE_OK, data=msg_param)

    def on_assist_connect(self, msg_req, param):
        try:
            s_id = param['sid']
            request_assist_id = param['request_assist_id']
            assist_id = param['assist_id']
            assist_ver = param['assist_ver']
        except Exception as e:
            log.e(e.__str__())
            return

        msg_req.caller.set_assist_id(assist_id)

        with self._lock:
            if assist_id in self._assists:
                assist_info = self._assists[assist_id]
            else:
                assist_info = AssistInfo()
                assist_info.assist_id = assist_id
                self._assists[assist_id] = assist_info

            assist_info.assist_ws = msg_req.caller
            assist_info.assist_ver = assist_ver

            self._ws_assist[msg_req.caller] = assist_id
            self._sid_to_assist[s_id] = assist_id

            # notify the web-client that assist connected.
            self._on_assist_info_changed(assist_info, request_assist_id)

    def _on_assist_info_changed(self, assist_info, request_assist_id):
        param = {'assist_id': assist_info.assist_id, 'assist_ver': assist_info.assist_ver}
        with self._lock:
            for caller in self._ws_web:
                if self._ws_web[caller] == assist_info.assist_id or self._ws_web[caller] == request_assist_id:
                    log.v('ws-web bind assist-id: {} -> {}\n'.format(request_assist_id, assist_info.assist_id))
                    assist_msg = AssistMessage(assist_info.assist_ws, 'update_assist_info')
                    self._ws_web[caller] = assist_info.assist_id
                    caller.set_assist_id(assist_info.assist_id)
                    caller.send_response(assist_msg, TPE_OK, data=param)

    def on_disconnect(self, caller):
        log.d('assist-ws {} disconnected\n'.format(caller.assist_id))
        with self._lock:
            if caller.client_type == AssistInfo.WS_CLIENT_WEB:
                if caller in self._ws_web:
                    del self._ws_web[caller]
                    return
            elif caller.client_type == AssistInfo.WS_CLIENT_ASSIST:
                if caller not in self._ws_assist:
                    log.e('assist-ws {} disconnected, but not in charge.\n'.format(caller.assist_id))
                    return
                assist_id = self._ws_assist[caller]
                del self._ws_assist[caller]
                if assist_id in self._assists:
                    del self._assists[assist_id]

                need_remove = list()
                for sid in self._sid_to_assist:
                    if self._sid_to_assist[sid] == assist_id:
                        need_remove.append(sid)
                for sid in need_remove:
                    del self._sid_to_assist[sid]

                # 通知相关的web页面，绑定的助手已经退出了
                for c in self._ws_web:
                    if self._ws_web[c] == assist_id:
                        assist_msg = AssistMessage(caller, 'assist_disconnected')
                        msg_param = {'assist_id': assist_id}
                        c.send_response(assist_msg, TPE_OK, data=msg_param)

    def on_request(self, msg_req: AssistMessage, param):
        with self._lock:
            if msg_req.caller.client_type == AssistInfo.WS_CLIENT_WEB:
                assist_id = self._ws_web[msg_req.caller] if msg_req.caller in self._ws_web else 0
                if assist_id != 0:
                    assist_info = self._assists[assist_id] if assist_id in self._assists else None
                    if assist_info is not None:
                        # assist_info.assist_ws.send_request(msg_req, param)
                        msg_req.send_request(assist_info.assist_ws, param)
                        return
                log.e('caller not bind assist.\n')
            elif msg_req.caller.client_type == AssistInfo.WS_CLIENT_ASSIST:
                log.w('got request from assist ?!\n')

    def forward_response(self, caller, msg):
        with self._lock:
            if caller.client_type == AssistInfo.WS_CLIENT_WEB:
                log.w('got response from web ?!\n')
            elif caller.client_type == AssistInfo.WS_CLIENT_ASSIST:
                message_id = msg['command_id']
                msg_req = self._commands[message_id] if message_id in self._commands else None
                if msg_req is None:
                    log.e('got response but command_id {} not known.\n'.format(message_id))
                    return
                if msg_req.caller is None:
                    log.e('got response but caller unknown.\n')
                    return
                msg_req.caller.send_response(msg_req, msg['code'], msg['message'], msg['data'])

                # remove finished message
                log.d('remove message, cmd_id={}\n'.format(msg_req.cmd_id))
                del self._commands[msg_req.cmd_id]


def tp_assist_bridge() -> TPAssistBridge:
    """取得 TPAssistBridge 管理器的唯一实例
    """

    import builtins
    if '__tp_assist_bridge__' not in builtins.__dict__:
        builtins.__dict__['__tp_assist_bridge__'] = TPAssistBridge()
    return builtins.__dict__['__tp_assist_bridge__']
