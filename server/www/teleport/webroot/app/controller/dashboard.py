# -*- coding: utf-8 -*-

from app.const import *
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.model import stats


class IndexHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_LOGIN_WEB)
        if ret != TPE_OK:
            return

        self.render('dashboard/index.mako')
