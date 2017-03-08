# -*- coding: utf-8 -*-

import os
import random
import io

import json
import urllib.parse
import tornado.gen
import tornado.httpclient

from wheezy.captcha.image import background
from wheezy.captcha.image import captcha
from wheezy.captcha.image import curve
from wheezy.captcha.image import noise
from wheezy.captcha.image import offset
from wheezy.captcha.image import rotate
from wheezy.captcha.image import smooth
from wheezy.captcha.image import text
from wheezy.captcha.image import warp

from .configs import app_cfg

cfg = app_cfg()

__all__ = ['async_post_http', 'async_enc']


@tornado.gen.coroutine
def async_post_http(post_data):
    try:
        v = json.dumps(post_data)
        data = urllib.parse.quote(v).encode('utf-8')

        c = tornado.httpclient.AsyncHTTPClient()
        r = yield c.fetch(cfg.core_server_rpc, body=data, method='POST')

        # print('async_post_http return:', r.body.decode())
        return json.loads(r.body.decode())
    except:
        return None


@tornado.gen.coroutine
def async_enc(data):
    # ts_server_rpc_ip = cfg.core.rpc.ip
    # ts_server_rpc_port = cfg.core.rpc.port

    # url = 'http://{}:{}/rpc'.format(ts_server_rpc_ip, ts_server_rpc_port)
    req = {'method': 'enc', 'param': {'p': data}}

    _yr = async_post_http(req)
    return_data = yield _yr
    if return_data is None:
        return {'code': -2}
    if 'code' not in return_data:
        return {'code': -3}
    if return_data['code'] != 0:
        return {'code': return_data['code']}

    if 'data' not in return_data:
        return {'code': -5}

    if 'c' not in return_data['data']:
        return {'code': -6}

    return {'code': 0, 'data': return_data['data']['c']}


_chars = 'ACDEFHJKLMNPQRTVWXY34679'


def gen_captcha():
    _font_dir = os.path.join(cfg.res_path, 'fonts')
    captcha_image_t = captcha(
        width=136,
        height=36,
        drawings=[
            background(color='#eeeeee'),
            text(fonts=[
                os.path.join(_font_dir, '001.ttf')
            ],
                font_sizes=(28, 34, 36, 32),
                color='#63a8f5',
                squeeze_factor=1.1,
                drawings=[
                    warp(dx_factor=0.05, dy_factor=0.05),
                    rotate(angle=15),
                    offset()
                ]),
            curve(color='#af6fff', width=2, number=9),
            noise(),
            smooth()
        ])

    chars_t = random.sample(_chars, 4)
    image = captcha_image_t(chars_t)

    out = io.BytesIO()
    image.save(out, "jpeg", quality=90)
    # web.header('Content-Type','image/jpeg')
    return ''.join(chars_t), out.getvalue()
