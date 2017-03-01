# -*- coding: utf-8 -*-
# import sys
# import tornado.ioloop
from .base import SwxBaseHandler


class IndexHandler(SwxBaseHandler):
    def get(self):
        self.render('maintenance/index.mako')

