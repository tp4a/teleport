# -*- coding: utf-8 -*-

import os
import random
import io
import hashlib

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

__all__ = ['async_post_http', 'async_enc', 'gen_captcha', 'sec_generate_password', 'sec_verify_password']


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


_captcha_chars = 'AaCDdEeFfHJjKkLMmNnPpQRTtVvWwXxYy34679'
# _font_dir = os.path.join(cfg.res_path, 'fonts')


def gen_captcha():
    captcha_image_t = captcha(
        width=136,
        height=36,
        drawings=[
            background(color='#eeeeee'),
            # curve(color='#4388d5', width=1, number=10),
            curve(color='#4388d5', width=1, number=10),
            curve(color='#af6fff', width=3, number=16),
            noise(number=80, color='#eeeeee', level=3),
            text(fonts=[
                os.path.join(cfg.res_path, 'fonts', '001.ttf')
            ],
                # font_sizes=(28, 34, 36, 32),
                font_sizes=(34, 38, 32),
                color='#63a8f5',
                # squeeze_factor=1.2,
                squeeze_factor=0.9,
                drawings=[
                    # warp(dx_factor=0.05, dy_factor=0.05),
                    warp(dx_factor=0.03, dy_factor=0.03),
                    rotate(angle=20),
                    offset()
                ]),
            # curve(color='#af6fff', width=3, number=16),
            noise(number=30, color='#eeeeee', level=2),
            smooth(),
        ])

    chars_t = random.sample(_captcha_chars, 4)
    image = captcha_image_t(chars_t)

    out = io.BytesIO()
    image.save(out, "jpeg", quality=100)
    # web.header('Content-Type','image/jpeg')
    return ''.join(chars_t), out.getvalue()


_hex_chars = '0123456789abcdef'


def sec_generate_password(password):
    """
    根据设置的password，计算一个加盐的散列，用于保存到数据库
    @param password: string
    @return: string
    """

    _hash_type = '3'        # 1 = md5, 2 = sha1, 3 = sha256

    _salt_data = list()
    for i in range(16):
        _salt_data.append(random.choice(_hex_chars))
    _salt = ''.join(_salt_data)

    h = hashlib.sha256()
    h.update(_hash_type.encode())
    h.update(_salt.encode())
    h.update(password.encode())
    _val = h.hexdigest()

    ret = '{}:{}:{}'.format(_hash_type, _salt, _val)

    print(ret, len(ret))
    return ret


def sec_verify_password(password, sec_password):
    _sec = sec_password.split(':')
    if len(_sec) != 3:
        return False

    if _sec[0] == '1':
        h = hashlib.md5()
    elif _sec[0] == '2':
        h = hashlib.sha1()
    elif _sec[0] == '3':
        h = hashlib.sha256()
    else:
        return False

    h.update(_sec[0].encode())
    h.update(_sec[1].encode())
    h.update(password.encode())
    _val = h.hexdigest()

    return _val == _sec[2]
