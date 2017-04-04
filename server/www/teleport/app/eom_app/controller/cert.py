# -*- coding: utf-8 -*-

from eom_app.app.configs import app_cfg
from eom_app.module import host
from .base import TPBaseAdminAuthHandler, TPBaseAdminAuthJsonHandler

cfg = app_cfg()


class IndexHandler(TPBaseAdminAuthHandler):
    def get(self):
        self.render('cert/index.mako')


class GetListHandler(TPBaseAdminAuthJsonHandler):
    def post(self):
        _certs = host.get_cert_list()
        ret = dict()
        ret['page_index'] = 10
        ret['total'] = len(_certs)
        ret['data'] = _certs
        self.write_json(0, data=ret)
