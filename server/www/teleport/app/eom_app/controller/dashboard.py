# -*- coding: utf-8 -*-

import tornado.ioloop
from .base import TPBaseAdminAuthHandler


class IndexHandler(TPBaseAdminAuthHandler):
    def get(self):
        self.render('dashboard/index.mako')
