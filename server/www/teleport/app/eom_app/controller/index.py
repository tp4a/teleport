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
