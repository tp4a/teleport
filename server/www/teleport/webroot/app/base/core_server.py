# -*- coding: utf-8 -*-

import json
import urllib.parse
import tornado.gen
import tornado.httpclient

from .configs import tp_cfg
from app.const import *
from app.base.logger import log

__all__ = ['core_service_async_post_http', 'core_service_async_enc']


@tornado.gen.coroutine
def core_service_async_post_http(post_data):
    try:
        v = json.dumps(post_data)
        data = urllib.parse.quote(v).encode('utf-8')

        c = tornado.httpclient.AsyncHTTPClient()
        r = yield c.fetch(tp_cfg().common.core_server_rpc, body=data, method='POST')

        # print('async_post_http return:', r.body.decode())
        # return TPE_OK, json.loads(r.body.decode())
        ret = json.loads(r.body.decode())
        # print('core_service_async_post_http::', ret)
        if 'code' not in ret:
            return TPE_FAILED, None
        if 'data' not in ret:
            return ret['code'], None
        return ret['code'], ret['data']
    except:
        log.e('core_service_async_post_http() failed.\n')
        return TPE_NO_CORE_SERVER, None


@tornado.gen.coroutine
def core_service_async_enc(data):

    req = {'method': 'enc', 'param': {'p': data}}

    _yr = core_service_async_post_http(req)
    code, ret_data = yield _yr
    if code != TPE_OK:
        return code, None
    if ret_data is None:
        return TPE_FAILED, None
    # if 'code' not in ret_data:
    #     return TPE_FAILED, None
    # if ret_data['code'] != TPE_OK:
    #     return ret_data['code'], None
    #
    # if 'data' not in ret_data:
    #     return TPE_FAILED, None

    if 'c' not in ret_data:
        return TPE_FAILED, None

    return TPE_OK, ret_data['c']
