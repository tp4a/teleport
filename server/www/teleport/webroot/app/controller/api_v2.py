# -*- coding: utf-8 -*-

import hmac
import base64
import hashlib
import json
from Crypto.Cipher import AES

import tornado.gen
from app.const import *
from app.model import host
from app.base.logger import *
from app.base.controller import TPBaseJsonHandler
from app.base.utils import tp_bin, tp_str, tp_timestamp_sec
from app.base.extsrv import tp_ext_srv_cfg
from .ops import api_v2_request_session_id


def pkcs7unpadding(data):
    length = len(data)
    pad_len = ord(data[length - 1])
    for i in range(pad_len):
        if ord(data[length - 1 - i]) != pad_len:
            return False, None
    return True, data[0:length - pad_len]


@tornado.gen.coroutine
def _parse_api_args(handler):
    raw_req = handler.request.body.decode('utf-8')
    if raw_req == '':
        return False, handler.write_json(TPE_PARAM)

    try:
        raw_req = json.loads(raw_req)

        if 'auth' not in raw_req or 'arg' not in raw_req or 'sign' not in raw_req:
            return False, handler.write_json(TPE_PARAM)
    except:
        return False, handler.write_json(TPE_JSON_FORMAT)

    _auth = raw_req['auth'].split(':')
    if len(_auth) <= 1:
        return False, handler.write_json(TPE_PARAM)

    if _auth[0] == '2':  # 目前的API请求格式版本为1
        if len(_auth) != 4:  # VERSION:ACCESS_KEY:TIMESTAMP:EXPIRES
            return False, handler.write_json(TPE_PARAM)
        req_access_key = _auth[1]
        req_timestamp = int(_auth[2])
        req_expires = int(_auth[3])
    else:
        return False, handler.write_json(TPE_PARAM)

    # 从数据库中根据access-key查找access-secret
    sec_info = tp_ext_srv_cfg().get_secret_info(req_access_key)
    if sec_info is None:
        return False, handler.write_json(TPE_INVALID_API_KEY)
    access_secret = sec_info['secret']

    # 是否超时
    # if tp_timestamp_sec() > req_timestamp + req_expires:
    #     return False, handler.write_json(TPE_EXPIRED)

    # 验证
    be_sign = '{}|{}'.format(raw_req['auth'], raw_req['arg'])
    _h = hmac.new(tp_bin(access_secret), tp_bin(be_sign), hashlib.sha1)
    _s = base64.urlsafe_b64decode(tp_bin(raw_req['sign']))
    if _s != _h.digest():
        return False, handler.write_json(TPE_INVALID_API_SIGN)

    enc_data = base64.urlsafe_b64decode(tp_bin(raw_req['arg']))

    # 解密
    hash_sha1 = hashlib.sha1()
    hash_sha1.update(tp_bin(raw_req['auth']))
    iv = hash_sha1.digest()[:16]
    hash_sha1 = hashlib.sha1()
    hash_sha1.update(tp_bin(access_secret))
    key = hash_sha1.digest()[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    dec_data = cipher.decrypt(enc_data)
    ok, dec_arg = pkcs7unpadding(tp_str(dec_data))
    if not ok:
        return False, handler.write_json(TPE_INVALID_API_SIGN)

    # 一切都OK，解码得到实际参数
    # _param = base64.urlsafe_b64decode(tp_bin(dec_arg))
    try:
        # args = json.loads(tp_str(_param))
        args = json.loads(dec_arg)
    except:
        return False, handler.write_json(TPE_JSON_FORMAT)

    args['_srv_name_'] = sec_info['name']

    return True, args


class RequestSessionHandler(TPBaseJsonHandler):

    @tornado.gen.coroutine
    def post(self):
        ok, args = yield _parse_api_args(self)
        if not ok:
            return

        try:
            operator = args['operator']
            remote_ip = args['remote_ip']
            remote_port = args['remote_port']
            remote_auth_type = args['remote_auth_type']
            remote_user = args['remote_user']
            remote_secret = args['remote_secret']
            protocol_type = args['protocol_type']
            protocol_sub_type = args['protocol_sub_type']
        except:
            return self.write_json(TPE_PARAM)

        operator = '[{}] {}'.format(args['_srv_name_'], operator)

        ret = yield api_v2_request_session_id(
            remote_ip, remote_port, remote_auth_type, remote_user, remote_secret,
            protocol_type, protocol_sub_type, self.request.remote_ip, operator
        )

        if ret['code'] != TPE_OK:
            return self.write_json(ret['code'], ret['message'])

        return self.write_json(TPE_OK, data=ret['data'])
