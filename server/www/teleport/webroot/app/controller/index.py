# -*- coding: utf-8 -*-

import tornado.ioloop
from app.base.controller import TPBaseHandler
from app.base.logger import log
from app.const import *
from tornado.escape import json_encode


class IndexHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_LOGIN_WEB)
        if ret != TPE_OK:
            return

        up = self._user['privilege']

        if (up & TP_PRIVILEGE_SYS_CONFIG) != 0:
            return self.redirect('/dashboard')
        elif (up & TP_PRIVILEGE_OPS) != 0:
            return self.redirect('/ops/remote')

        self.redirect('/user/me')


class CatchAllHandler(TPBaseHandler):
    def get(self):
        log.w('catch all, GET: {}\n'.format(self.request.uri))
        self.show_error_page(TPE_HTTP_404_NOT_FOUND)

    def post(self):
        log.w('catch all, POST: {}\n'.format(self.request.uri))
        _ret = {'code': TPE_HTTP_404_NOT_FOUND, 'message': '错误的URI', 'data': {}}
        self.set_header("Content-Type", "application/json")
        self.write(json_encode(_ret))
        self.finish()


class ExitHandler(TPBaseHandler):
    def get(self):
        self.write('exit ok')
        tornado.ioloop.IOLoop.instance().stop()
