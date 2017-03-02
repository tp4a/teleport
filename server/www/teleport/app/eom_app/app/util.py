# -*- coding: utf-8 -*-

import json
import urllib.parse
import tornado.gen
import tornado.httpclient

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
