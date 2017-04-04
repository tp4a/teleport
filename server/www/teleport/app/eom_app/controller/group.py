# -*- coding: utf-8 -*-

from eom_app.app.configs import app_cfg
from eom_app.module import host
from .base import TPBaseAdminAuthHandler, TPBaseAdminAuthJsonHandler

cfg = app_cfg()


class IndexHandler(TPBaseAdminAuthHandler):
    def get(self):
        self.render('group/index.mako')


class GetListHandler(TPBaseAdminAuthJsonHandler):
    def post(self):
        group_list = host.get_group_list()
        ret = dict()
        ret['page_index'] = 10
        ret['total'] = len(group_list)
        ret['data'] = group_list
        self.write_json(0, data=ret)
