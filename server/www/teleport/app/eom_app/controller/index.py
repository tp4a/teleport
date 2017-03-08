# -*- coding: utf-8 -*-
import sys
import tornado.ioloop
from .base import SwxBaseHandler, SwxAuthHandler


class IndexHandler(SwxAuthHandler):
    def get(self):
        self.redirect('/host')


class ExitHandler(SwxBaseHandler):
    def get(self):
        self.write('exit ok')
        tornado.ioloop.IOLoop.instance().stop()
