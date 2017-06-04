# -*- coding: utf-8 -*-
import sys
import tornado.ioloop
from .base import TPBaseHandler, TPBaseUserAuthHandler


class IndexHandler(TPBaseUserAuthHandler):
    def get(self):
        self.redirect('/host')


class ExitHandler(TPBaseHandler):
    def get(self):
        self.write('exit ok')
        tornado.ioloop.IOLoop.instance().stop()


class UIDesignHandler(TPBaseHandler):
    def get(self):
        self.render('uidesign/index.mako')


class UIDesignWithoutSidebarHandler(TPBaseHandler):
    def get(self):
        self.render('uidesign/without-sidebar.mako')


class UIDesignTableHandler(TPBaseHandler):
    def get(self):
        # from hashlib import sha1
        # import hmac
        # my_sign = hmac.new('key', 'msg', sha1).digest()
        # # my_sign = base64.b64encode(my_sign)
        # # print my_sign

        self.render('uidesign/table.mako')

