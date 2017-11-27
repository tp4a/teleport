# -*- coding: utf-8 -*-

from app.const import *
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.model import stat


class IndexHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_LOGIN_WEB)
        if ret != TPE_OK:
            return

        self.render('dashboard/index.mako')


class DoGetBasicHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_LOGIN_WEB)
        if ret != TPE_OK:
            return

        err, info = stat.get_basic()
        if err != TPE_OK:
            return self.write_json(err)

        # ret = dict()
        # ret['count_user'] = 5
        # ret['count_host'] = 5
        # ret['count_acc'] = 5
        # ret['count_conn'] = 5
        self.write_json(TPE_OK, data=info)

