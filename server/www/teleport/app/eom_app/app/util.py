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

__all__ = ['async_post_http']


@tornado.gen.coroutine
def async_post_http(url, values):
    try:
        v = json.dumps(values)
        data = urllib.parse.quote(v).encode('utf-8')

        c = tornado.httpclient.AsyncHTTPClient()
        r = yield c.fetch(url, body=data, method='POST')

        return json.loads(r.body.decode())

        # return r.body
    except:
        # return {'code': -2, 'message': 'can not fetch {}'.format(url)}
        return None


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
