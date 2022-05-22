# -*- coding: utf-8 -*-

import json
from app.const import *
from app.base.controller import TPBaseHandler
from ._sidebar_menu import tp_generate_sidebar


class IndexHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_LOGIN_WEB)
        if ret != TPE_OK:
            return

        self.render('dashboard/index.html', sidebar_menu=tp_generate_sidebar(self))
